# bedrock-to-java-texture

将 Minecraft 基岩版资源包（`.mcpack` 或文件夹）转换为 Java 版（1.20.1）资源包的工具，支持 **CLI** 与 **GUI**，并支持打包成 EXE。

## 功能

- 目录重组：`textures/blocks -> assets/minecraft/textures/block`、`textures/items -> .../item`。
- 自动生成 `pack.mcmeta`（`pack_format: 15`，对应 Java 1.20.1）。
- 读取 `manifest.json` 的描述写入 `pack.mcmeta`。
- 内置核心 Bedrock -> Java 纹理重命名字典（如 `grass_side -> grass_block_side`）。
- 读取 `textures/terrain_texture.json` + `textures/item_texture.json` 的短路径映射，并映射到 Java 目标路径。
- 支持 `.tga -> .png`（依赖 Pillow）。
- GUI 支持选择输入文件/目录和输出路径。

## 运行依赖

- Python 3.9+
- tkinter
- Pillow（用于 `.tga`）

## 将 Pillow 直接放进仓库（离线可用）

项目运行时会自动把 `./vendor` 加入 `sys.path`。

```bash
python3 -m pip install --target ./vendor pillow
```

> 如果你要发布给其他用户（含 EXE），请确保最终产物里也包含 `vendor/PIL`。

## CLI 用法

```bash
python3 convert_mcpack.py <input_mcpack_or_folder_or_batch_folder> -o ./converted
```

启动 GUI：

```bash
python3 convert_mcpack.py --gui
# 或
python3 convert_mcpack_gui.py
```

## 打包 EXE（PyInstaller）

安装构建依赖：

```bash
python3 -m pip install -r requirements-build.txt
```

执行构建脚本：

```bash
python3 build_exe.py
```

默认输出：

- `dist/bedrock_to_java_converter/`（onedir）

该构建会自动把 `vendor/` 一并带上（`--add-data`），因此 vendored Pillow 可随 EXE 一起分发。
