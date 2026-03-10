#!/usr/bin/env python3
"""
Convert Minecraft Bedrock resource packs (.mcpack or folders) to Java 1.20.1 format.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    from PIL import Image
except ImportError:  # optional dependency for TGA conversion
    Image = None

PACK_FORMAT_1_20_1 = 15

# Core name mapping differences between Bedrock and Java.
TEXTURE_RENAME_MAP = {
    "grass_side": "grass_block_side",
    "grass_side_carried": "grass_block_side_overlay",
    "grass_top": "grass_block_top",
    "leaves_oak": "oak_leaves",
    "log_oak": "oak_log",
    "planks_oak": "oak_planks",
    "stonebrick": "stone_bricks",
}

# Bedrock directory names to Java directory names under assets/minecraft/textures.
CATEGORY_MAP = {
    "blocks": "block",
    "items": "item",
    "entity": "entity",
    "environment": "environment",
    "gui": "gui",
    "models": "models",
    "particle": "particle",
    "ui": "gui",
}


@dataclass
class PackContext:
    source_path: Path
    extracted_root: Path
    output_path: Path


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s")


def read_json(path: Path) -> Optional[dict]:
    if not path.exists():
        logging.warning("JSON file not found: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.error("Failed to parse JSON %s: %s", path, exc)
        return None


def extract_mcpack(mcpack_file: Path) -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="mcpack_convert_"))
    with zipfile.ZipFile(mcpack_file, "r") as zf:
        zf.extractall(temp_dir)
    logging.info("Extracted %s -> %s", mcpack_file, temp_dir)
    return temp_dir


def resolve_pack_root(extracted_root: Path) -> Path:
    manifest_here = extracted_root / "manifest.json"
    if manifest_here.exists():
        return extracted_root

    for candidate in extracted_root.iterdir():
        if candidate.is_dir() and (candidate / "manifest.json").exists():
            return candidate

    return extracted_root


def manifest_description(manifest: Optional[dict]) -> str:
    if not manifest:
        return "Converted from Bedrock resource pack"

    header = manifest.get("header", {})
    desc = header.get("description")
    name = header.get("name")

    if isinstance(desc, str) and desc.strip():
        return desc.strip()
    if isinstance(name, str) and name.strip():
        return f"Converted from Bedrock pack: {name.strip()}"
    return "Converted from Bedrock resource pack"


def create_pack_mcmeta(output_pack: Path, description: str) -> None:
    payload = {
        "pack": {
            "pack_format": PACK_FORMAT_1_20_1,
            "description": description,
        }
    }
    target = output_pack / "pack.mcmeta"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logging.info("Generated %s", target)


def load_bedrock_texture_mappings(pack_root: Path) -> Dict[str, str]:
    mappings: Dict[str, str] = {}
    textures_dir = pack_root / "textures"

    for file_name in ("terrain_texture.json", "item_texture.json"):
        data = read_json(textures_dir / file_name)
        if not data:
            continue

        texture_data = data.get("texture_data", {})
        for short_name, detail in texture_data.items():
            path_value: Optional[str] = None
            if isinstance(detail, dict):
                textures = detail.get("textures")
                if isinstance(textures, str):
                    path_value = textures
                elif isinstance(textures, list) and textures:
                    first = textures[0]
                    if isinstance(first, str):
                        path_value = first
                    elif isinstance(first, dict) and isinstance(first.get("path"), str):
                        path_value = first["path"]
                elif isinstance(textures, dict) and isinstance(textures.get("path"), str):
                    path_value = textures["path"]

            if path_value:
                mappings[short_name] = path_value

    logging.info("Loaded %d short-path mappings from Bedrock metadata", len(mappings))
    return mappings


def normalize_texture_name(name: str) -> str:
    stem = name.replace("\\", "/").split("/")[-1]
    return TEXTURE_RENAME_MAP.get(stem, stem)


def convert_tga_to_png(src: Path, dst: Path) -> None:
    if Image is None:
        raise RuntimeError("Pillow is required for .tga conversion. Install with: pip install pillow")

    with Image.open(src) as img:
        img.save(dst, format="PNG")


def copy_texture_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)

    if src.suffix.lower() == ".tga":
        png_target = dst.with_suffix(".png")
        try:
            convert_tga_to_png(src, png_target)
            logging.info("Converted TGA -> PNG: %s -> %s", src, png_target)
        except Exception as exc:
            logging.error("Failed TGA conversion for %s: %s", src, exc)
        return

    shutil.copy2(src, dst)
    logging.debug("Copied %s -> %s", src, dst)


def map_destination_relative(path_under_textures: Path) -> Path:
    parts = list(path_under_textures.parts)
    if not parts:
        return path_under_textures

    first = parts[0]
    mapped_first = CATEGORY_MAP.get(first, first)
    return Path(mapped_first, *parts[1:])


def build_short_path_index(textures_dir: Path) -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for file in textures_dir.rglob("*"):
        if not file.is_file():
            continue
        if file.suffix.lower() not in {".png", ".tga"}:
            continue
        rel_no_suffix = str(file.relative_to(textures_dir).with_suffix("")).replace("\\", "/")
        idx[rel_no_suffix] = file
        idx[file.stem] = file
    return idx


def apply_short_path_mappings(
    bedrock_mappings: Dict[str, str],
    textures_index: Dict[str, Path],
    java_textures_root: Path,
) -> None:
    for short_name, short_path in bedrock_mappings.items():
        source = textures_index.get(short_path) or textures_index.get(short_name)
        if not source:
            logging.warning("No source file found for short mapping: %s -> %s", short_name, short_path)
            continue

        normalized_name = normalize_texture_name(short_name)
        guessed_category = "item" if "item" in short_path else "block"
        destination = java_textures_root / guessed_category / f"{normalized_name}{source.suffix.lower()}"
        copy_texture_file(source, destination)


def move_gui_fragments(textures_dir: Path, java_textures_root: Path) -> None:
    gui_dir = textures_dir / "gui"
    if not gui_dir.exists():
        return

    for src in gui_dir.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in {".png", ".tga"}:
            continue
        rel = src.relative_to(gui_dir)
        dst = java_textures_root / "gui" / "container" / rel
        copy_texture_file(src, dst)


def transfer_textures(pack_root: Path, output_pack: Path) -> None:
    textures_dir = pack_root / "textures"
    if not textures_dir.exists():
        logging.warning("No textures directory found in %s", pack_root)
        return

    java_textures_root = output_pack / "assets" / "minecraft" / "textures"
    java_textures_root.mkdir(parents=True, exist_ok=True)

    for src in textures_dir.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in {".png", ".tga"}:
            continue

        relative = src.relative_to(textures_dir)
        mapped_relative = map_destination_relative(relative)

        new_stem = normalize_texture_name(mapped_relative.stem)
        mapped_relative = mapped_relative.with_name(new_stem + mapped_relative.suffix)
        dst = java_textures_root / mapped_relative
        copy_texture_file(src, dst)

    short_mappings = load_bedrock_texture_mappings(pack_root)
    texture_index = build_short_path_index(textures_dir)
    apply_short_path_mappings(short_mappings, texture_index, java_textures_root)

    move_gui_fragments(textures_dir, java_textures_root)


def copy_pack_icon(pack_root: Path, output_pack: Path) -> None:
    candidates = [pack_root / "pack_icon.png", pack_root / "pack.png"]
    for icon in candidates:
        if icon.exists():
            shutil.copy2(icon, output_pack / "pack.png")
            logging.info("Copied icon %s -> %s", icon, output_pack / "pack.png")
            return


def convert_pack(source: Path, output_dir: Path, keep_temp: bool = False) -> None:
    temp_root: Optional[Path] = None

    if source.is_file() and source.suffix.lower() == ".mcpack":
        temp_root = extract_mcpack(source)
        extracted = resolve_pack_root(temp_root)
        pack_name = source.stem
    elif source.is_dir():
        extracted = source
        pack_name = source.name
    else:
        raise FileNotFoundError(f"Unsupported input path: {source}")

    output_pack = output_dir / pack_name
    output_pack.mkdir(parents=True, exist_ok=True)

    manifest = read_json(extracted / "manifest.json")
    description = manifest_description(manifest)
    create_pack_mcmeta(output_pack, description)
    transfer_textures(extracted, output_pack)
    copy_pack_icon(extracted, output_pack)

    logging.info("Converted pack: %s -> %s", source, output_pack)

    if temp_root and not keep_temp:
        shutil.rmtree(temp_root, ignore_errors=True)


def discover_inputs(path: Path) -> Iterable[Path]:
    if path.is_file():
        return [path]

    if not path.is_dir():
        return []

    results: List[Path] = []
    for child in path.iterdir():
        if child.is_file() and child.suffix.lower() == ".mcpack":
            results.append(child)
        elif child.is_dir() and ((child / "manifest.json").exists() or (child / "textures").exists()):
            results.append(child)

    return sorted(results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Bedrock texture packs to Java 1.20.1 resource packs")
    parser.add_argument("input", type=Path, help="Input .mcpack file, Bedrock pack directory, or a directory for batch conversion")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted_packs"), help="Output directory")
    parser.add_argument("--keep-temp", action="store_true", help="Keep extracted temp folders for mcpack inputs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")

    args = parser.parse_args()
    setup_logging(args.verbose)

    inputs = list(discover_inputs(args.input))
    if not inputs:
        logging.error("No valid inputs found at %s", args.input)
        raise SystemExit(1)

    logging.info("Found %d input(s) for conversion", len(inputs))
    args.output.mkdir(parents=True, exist_ok=True)

    failures = 0
    for src in inputs:
        try:
            convert_pack(src, args.output, keep_temp=args.keep_temp)
        except Exception as exc:
            failures += 1
            logging.exception("Failed to convert %s: %s", src, exc)

    if failures:
        logging.error("Completed with %d failure(s)", failures)
        raise SystemExit(2)

    logging.info("All conversions completed successfully")


if __name__ == "__main__":
    main()
