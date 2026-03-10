# bedrock-to-java-texture

A Python tool for converting Minecraft Bedrock Edition texture packs (`.mcpack` or folders) into Java Edition (1.20.1) resource packs.

## Features

- Reorganizes Bedrock `textures/` files into Java structure (`assets/minecraft/textures/...`).
- Generates `pack.mcmeta` automatically (`pack_format: 15` for Java 1.20.1).
- Extracts description data from `manifest.json` and writes it into `pack.mcmeta`.
- Handles common texture naming differences (e.g. `grass_side` -> `grass_block_side`).
- Reads `textures/terrain_texture.json` and `textures/item_texture.json` short-path entries and maps them to Java texture locations.
- Converts `.tga` textures to `.png` automatically (requires Pillow).
- Includes initial GUI fragment handling by moving Bedrock GUI pieces under Java `gui/container`.
- Supports batch conversion for multiple packs in one command.

## Requirements

- Python 3.9+
- Optional (for TGA conversion):

```bash
pip install pillow
```

## Usage

Convert a single pack:

```bash
python3 convert_mcpack.py ./MyPack.mcpack -o ./converted
```

Convert a pack folder:

```bash
python3 convert_mcpack.py ./MyBedrockPack -o ./converted
```

Batch convert all `.mcpack` and pack folders directly inside a directory:

```bash
python3 convert_mcpack.py ./input_packs -o ./converted
```

Verbose log:

```bash
python3 convert_mcpack.py ./input_packs -o ./converted -v
```
