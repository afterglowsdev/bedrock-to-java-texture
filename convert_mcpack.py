#!/usr/bin/env python3
"""Bedrock -> Java resource-pack converter (CLI + GUI)."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PACK_FORMAT_1_20_1 = 15
TEXTURE_EXTENSIONS = {".png", ".tga"}

# Common Bedrock -> Java texture stem mappings (core set).
TEXTURE_RENAME_MAP = {
    "grass_side": "grass_block_side",
    "grass_side_carried": "grass_block_side_overlay",
    "grass_top": "grass_block_top",
    "grass_path_side": "dirt_path_side",
    "grass_path_top": "dirt_path_top",
    "coarse_dirt": "coarse_dirt",
    "stonebrick": "stone_bricks",
    "stonebrick_carved": "chiseled_stone_bricks",
    "stonebrick_cracked": "cracked_stone_bricks",
    "leaves_oak": "oak_leaves",
    "leaves_spruce": "spruce_leaves",
    "leaves_birch": "birch_leaves",
    "leaves_jungle": "jungle_leaves",
    "leaves_acacia": "acacia_leaves",
    "leaves_big_oak": "dark_oak_leaves",
    "log_oak": "oak_log",
    "log_spruce": "spruce_log",
    "log_birch": "birch_log",
    "log_jungle": "jungle_log",
    "log_acacia": "acacia_log",
    "log_big_oak": "dark_oak_log",
    "planks_oak": "oak_planks",
    "planks_spruce": "spruce_planks",
    "planks_birch": "birch_planks",
    "planks_jungle": "jungle_planks",
    "planks_acacia": "acacia_planks",
    "planks_big_oak": "dark_oak_planks",
    "reeds": "sugar_cane",
}

CATEGORY_MAP = {
    "blocks": "block",
    "items": "item",
    "item": "item",
    "entity": "entity",
    "environment": "environment",
    "gui": "gui",
    "models": "models",
    "particle": "particle",
    "ui": "gui",
}


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


def _bootstrap_vendor() -> None:
    vendor = _runtime_root() / "vendor"
    if vendor.exists() and str(vendor) not in sys.path:
        sys.path.insert(0, str(vendor))


_bootstrap_vendor()

try:
    from PIL import Image
except Exception:
    Image = None


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, format="[%(levelname)s] %(message)s")


def read_json(path: Path) -> Optional[dict]:
    if not path.exists():
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
    if (extracted_root / "manifest.json").exists():
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
    payload = {"pack": {"pack_format": PACK_FORMAT_1_20_1, "description": description}}
    (output_pack / "pack.mcmeta").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _extract_texture_path(detail: object) -> Optional[str]:
    if not isinstance(detail, dict):
        return None
    textures = detail.get("textures")
    if isinstance(textures, str):
        return textures
    if isinstance(textures, dict) and isinstance(textures.get("path"), str):
        return textures["path"]
    if isinstance(textures, list) and textures:
        first = textures[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict) and isinstance(first.get("path"), str):
            return first["path"]
    return None


def load_bedrock_texture_mappings(pack_root: Path) -> Dict[str, str]:
    mappings: Dict[str, str] = {}
    textures_dir = pack_root / "textures"
    for file_name in ("terrain_texture.json", "item_texture.json"):
        data = read_json(textures_dir / file_name)
        if not data:
            continue
        for short_name, detail in data.get("texture_data", {}).items():
            path_value = _extract_texture_path(detail)
            if path_value:
                mappings[str(short_name)] = path_value
    return mappings


def normalize_texture_name(name: str) -> str:
    stem = name.replace("\\", "/").split("/")[-1]
    return TEXTURE_RENAME_MAP.get(stem, stem)


def convert_tga_to_png(src: Path, dst: Path) -> None:
    if Image is None:
        raise RuntimeError("TGA conversion requires Pillow. Install or vendor Pillow in ./vendor")
    with Image.open(src) as img:
        img.save(dst, format="PNG")


def copy_texture_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() == ".tga":
        convert_tga_to_png(src, dst.with_suffix(".png"))
    else:
        shutil.copy2(src, dst)


def map_destination_relative(path_under_textures: Path) -> Path:
    parts = list(path_under_textures.parts)
    if not parts:
        return path_under_textures

    mapped_first = CATEGORY_MAP.get(parts[0].lower(), parts[0].lower())
    stem = normalize_texture_name(Path(parts[-1]).stem)
    filename = stem + Path(parts[-1]).suffix.lower()
    return Path(mapped_first, *parts[1:-1], filename)


def build_short_path_index(textures_dir: Path) -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for file in textures_dir.rglob("*"):
        if not file.is_file() or file.suffix.lower() not in TEXTURE_EXTENSIONS:
            continue
        rel = file.relative_to(textures_dir).with_suffix("")
        rel_key = str(rel).replace("\\", "/")
        idx[rel_key] = file
        idx[file.stem] = file
    return idx


def map_bedrock_short_path_to_java(short_path: str, fallback_short_name: str, source_suffix: str) -> Path:
    parts = short_path.replace("\\", "/").strip("/").split("/")

    if parts and parts[0] == "textures":
        parts = parts[1:]
    if not parts:
        return Path("block", normalize_texture_name(fallback_short_name) + source_suffix)

    first = CATEGORY_MAP.get(parts[0].lower(), parts[0].lower())
    tail = parts[1:]

    if tail:
        tail[-1] = normalize_texture_name(Path(tail[-1]).stem)
        return Path(first, *tail).with_suffix(source_suffix)

    return Path(first, normalize_texture_name(fallback_short_name) + source_suffix)


def apply_short_path_mappings(bedrock_mappings: Dict[str, str], textures_index: Dict[str, Path], java_textures_root: Path) -> None:
    for short_name, short_path in bedrock_mappings.items():
        source = textures_index.get(short_path) or textures_index.get(short_name)
        if not source:
            continue
        dst_rel = map_bedrock_short_path_to_java(short_path, short_name, source.suffix.lower())
        copy_texture_file(source, java_textures_root / dst_rel)


def move_gui_fragments(textures_dir: Path, java_textures_root: Path) -> None:
    gui_dir = textures_dir / "gui"
    if not gui_dir.exists():
        return
    for src in gui_dir.rglob("*"):
        if src.is_file() and src.suffix.lower() in TEXTURE_EXTENSIONS:
            copy_texture_file(src, java_textures_root / "gui" / "container" / src.relative_to(gui_dir))


def transfer_textures(pack_root: Path, output_pack: Path) -> None:
    textures_dir = pack_root / "textures"
    if not textures_dir.exists():
        logging.warning("No textures directory found in %s", pack_root)
        return

    java_textures_root = output_pack / "assets" / "minecraft" / "textures"
    java_textures_root.mkdir(parents=True, exist_ok=True)

    # 1) copy direct files with directory/filename normalization
    for src in textures_dir.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in TEXTURE_EXTENSIONS:
            continue
        dst_rel = map_destination_relative(src.relative_to(textures_dir))
        copy_texture_file(src, java_textures_root / dst_rel)

    # 2) apply atlas short-path mappings as overwrite/补充
    mappings = load_bedrock_texture_mappings(pack_root)
    apply_short_path_mappings(mappings, build_short_path_index(textures_dir), java_textures_root)

    # 3) GUI碎图兼容搬运
    move_gui_fragments(textures_dir, java_textures_root)


def copy_pack_icon(pack_root: Path, output_pack: Path) -> None:
    for icon in (pack_root / "pack_icon.png", pack_root / "pack.png"):
        if icon.exists():
            shutil.copy2(icon, output_pack / "pack.png")
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
    create_pack_mcmeta(output_pack, manifest_description(manifest))
    transfer_textures(extracted, output_pack)
    copy_pack_icon(extracted, output_pack)

    if temp_root and not keep_temp:
        shutil.rmtree(temp_root, ignore_errors=True)


def discover_inputs(path: Path) -> Iterable[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []

    # Single pack directory input
    if (path / "manifest.json").exists() or (path / "textures").exists():
        return [path]

    # Batch directory input
    results: List[Path] = []
    for child in path.iterdir():
        if child.is_file() and child.suffix.lower() == ".mcpack":
            results.append(child)
        elif child.is_dir() and ((child / "manifest.json").exists() or (child / "textures").exists()):
            results.append(child)
    return sorted(results)


def run_conversion(input_path: Path, output_path: Path, keep_temp: bool = False) -> None:
    inputs = list(discover_inputs(input_path))
    if not inputs:
        raise RuntimeError(f"No valid inputs found at {input_path}")
    output_path.mkdir(parents=True, exist_ok=True)

    failures = 0
    for src in inputs:
        try:
            convert_pack(src, output_path, keep_temp=keep_temp)
            logging.info("Converted: %s", src)
        except Exception as exc:
            failures += 1
            logging.exception("Failed to convert %s: %s", src, exc)

    if failures:
        raise RuntimeError(f"Conversion finished with {failures} failure(s)")


def run_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.title("Bedrock -> Java Resource Pack Converter")
    root.geometry("760x360")

    in_var = tk.StringVar()
    out_var = tk.StringVar(value=str((Path.cwd() / "converted_packs").resolve()))
    status_var = tk.StringVar(value="Ready")

    def browse_input_file() -> None:
        value = filedialog.askopenfilename(filetypes=[("Minecraft Pack", "*.mcpack"), ("All Files", "*")])
        if value:
            in_var.set(value)

    def browse_input_dir() -> None:
        value = filedialog.askdirectory()
        if value:
            in_var.set(value)

    def browse_output_dir() -> None:
        value = filedialog.askdirectory()
        if value:
            out_var.set(value)

    def start_convert() -> None:
        input_value = in_var.get().strip()
        output_value = out_var.get().strip()
        if not input_value or not output_value:
            messagebox.showerror("Missing path", "Please select both input and output paths.")
            return

        status_var.set("Converting...")

        def worker() -> None:
            try:
                run_conversion(Path(input_value), Path(output_value))
                root.after(0, lambda: status_var.set("Done"))
                root.after(0, lambda: messagebox.showinfo("Done", "Conversion completed successfully."))
            except Exception as exc:
                root.after(0, lambda: status_var.set("Failed"))
                root.after(0, lambda: messagebox.showerror("Conversion failed", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    frame = tk.Frame(root, padx=12, pady=12)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Input (.mcpack / pack folder / batch folder):", anchor="w").pack(fill="x")
    row1 = tk.Frame(frame)
    row1.pack(fill="x", pady=(4, 10))
    tk.Entry(row1, textvariable=in_var).pack(side="left", fill="x", expand=True)
    tk.Button(row1, text="选择文件", command=browse_input_file).pack(side="left", padx=4)
    tk.Button(row1, text="选择文件夹", command=browse_input_dir).pack(side="left")

    tk.Label(frame, text="Output folder:", anchor="w").pack(fill="x")
    row2 = tk.Frame(frame)
    row2.pack(fill="x", pady=(4, 16))
    tk.Entry(row2, textvariable=out_var).pack(side="left", fill="x", expand=True)
    tk.Button(row2, text="选择输出", command=browse_output_dir).pack(side="left", padx=4)

    tk.Button(frame, text="开始转换", command=start_convert, height=2).pack(fill="x")
    tk.Label(frame, textvariable=status_var, fg="blue", pady=10).pack(fill="x")
    tk.Label(
        frame,
        text="提示: TGA->PNG 需要 Pillow。打包 EXE 时请一并打包 vendor/ 目录。",
        fg="gray",
        wraplength=700,
        justify="left",
        anchor="w",
    ).pack(fill="x", pady=(16, 0))

    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Bedrock texture packs to Java 1.20.1 resource packs")
    parser.add_argument("input", nargs="?", type=Path, help="Input .mcpack, Bedrock pack folder, or batch folder")
    parser.add_argument("-o", "--output", type=Path, default=Path("converted_packs"), help="Output directory")
    parser.add_argument("--keep-temp", action="store_true", help="Keep extracted temp folders for mcpack inputs")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logs")
    parser.add_argument("--gui", action="store_true", help="Launch GUI")
    args = parser.parse_args()

    if args.gui:
        setup_logging(False)
        run_gui()
        return

    if not args.input:
        parser.error("input is required unless --gui is used")

    setup_logging(args.verbose)
    run_conversion(args.input, args.output, keep_temp=args.keep_temp)


if __name__ == "__main__":
    main()
