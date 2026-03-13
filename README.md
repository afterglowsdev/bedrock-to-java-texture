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

```bash
python3 convert_mcpack.py ./MyPack.mcpack -o ./converted
```

转换单个基岩包目录：

```bash
python3 convert_mcpack.py ./MyBedrockPack -o ./converted
```

批量转换目录：

```bash
python3 convert_mcpack.py ./input_packs -o ./converted
```

## GUI 用法

方式一：

```bash
python3 convert_mcpack.py --gui
```

方式二：

```bash
python3 convert_mcpack_gui.py
```
>>>>>>> main
