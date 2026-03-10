# bedrock-to-java-texture

<<<<<<< codex/create-script-to-convert-bedrock-to-java-resource-pack-cdow7e
一个用于将 Minecraft 基岩版资源包（`.mcpack` 或文件夹）转换为 Java 版（1.20.1）资源包结构的 Python 工具，包含 CLI 和 GUI。

## 功能

- 按 Java 资源包规范重组目录：`textures/blocks -> assets/minecraft/textures/block` 等。
- 自动生成 `pack.mcmeta`，并写入 `pack_format: 15`（Java 1.20.1）。
- 从 `manifest.json` 中提取包描述并写入 `pack.mcmeta`。
- 内置核心命名映射（如 `grass_side -> grass_block_side`）。
- 读取 `textures/terrain_texture.json`、`textures/item_texture.json`，处理短路径映射。
- 支持 `.tga -> .png`（需要 Pillow）。
- GUI 界面支持选择输入文件/文件夹与输出路径。
- 支持批量转换（目录下多个 `.mcpack` 或资源包文件夹）。

## 依赖

- Python 3.9+
- tkinter（大多数 Python 发行版默认自带）
- Pillow（用于 TGA 转 PNG）

## 将依赖直接放进仓库（离线/打包推荐）

项目会自动把 `./vendor` 加入 `sys.path`，可将 Pillow 直接安装到仓库中：

```bash
python3 -m pip install --target ./vendor pillow
```

这样打包成 exe/app 后无需运行时联网安装依赖。

## CLI 用法

单包转换：
=======
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
>>>>>>> main

```bash
python3 convert_mcpack.py ./MyPack.mcpack -o ./converted
```

<<<<<<< codex/create-script-to-convert-bedrock-to-java-resource-pack-cdow7e
转换单个基岩包目录：
=======
Convert a pack folder:
>>>>>>> main

```bash
python3 convert_mcpack.py ./MyBedrockPack -o ./converted
```

<<<<<<< codex/create-script-to-convert-bedrock-to-java-resource-pack-cdow7e
批量转换目录：
=======
Batch convert all `.mcpack` and pack folders directly inside a directory:
>>>>>>> main

```bash
python3 convert_mcpack.py ./input_packs -o ./converted
```

<<<<<<< codex/create-script-to-convert-bedrock-to-java-resource-pack-cdow7e
## GUI 用法

方式一：

```bash
python3 convert_mcpack.py --gui
```

方式二：

```bash
python3 convert_mcpack_gui.py
=======
Verbose log:

```bash
python3 convert_mcpack.py ./input_packs -o ./converted -v
>>>>>>> main
```
