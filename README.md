# obs2feishu

将 Obsidian Markdown 笔记转换为可直接导入飞书的 HTML 文件。

## 功能特性

- **Wiki 图片内嵌**：自动识别 Obsidian 的 `![[图片.png]]` 语法，在 Vault 中递归搜索图片并转为 Base64 内嵌，HTML 文件无需额外携带图片资源
- **Callout 转换**：将 Obsidian 的 `[!note]`、`[!warning]` 等 Callout 块转换为带颜色样式的 HTML 区块
- **多文件批量转换**：支持同时选择多个 `.md` 文件一键转换
- **自定义输出目录**：可指定 HTML 文件的输出位置，留空则输出到原文件同目录
- **转换完成快捷操作**：转换完成后可直接打开生成的 HTML 文件，或打开文件所在目录

## 依赖

### Pandoc

本工具依赖 [Pandoc](https://pandoc.org/installing.html) 进行 Markdown → HTML 转换，请先安装：

```bash
# 验证安装
pandoc --version
```

### Python 依赖

仅使用 Python 标准库，无需额外安装第三方包。Python 3.10+ 即可。

## 使用方法

### 启动 GUI

```bash
python obs2feishu_gui.py
```

### 操作步骤

1. **选择输入文件**：点击「选择文件…」，支持按住 Ctrl 或 Shift 多选 `.md` 文件
2. **确认 Vault 根目录**：默认已填入 `D:\Note_obsidian`，可按需修改（用于搜索笔记中引用的图片）
3. **选择输出目录（可选）**：留空则 HTML 文件输出到与 `.md` 文件相同的目录
4. **点击「▶ 开始转换」**：日志区实时显示转换进度
5. **转换完成后**：
   - 点击「📄 打开文件」直接打开生成的 HTML 文件（多文件时全部打开）
   - 点击「📁 打开所在目录」在资源管理器中定位到输出目录

### 导入飞书

将生成的 `.html` 文件直接导入飞书知识库即可。

## 文件结构

```
obs2feishu/
├── obs2feishu.py        # 核心转换逻辑（图片处理、Callout 转换、Pandoc 调用）
└── obs2feishu_gui.py    # 可视化界面
```

## 支持的 Obsidian 语法

| 语法 | 说明 |
|------|------|
| `![[image.png]]` | Wiki 图片嵌入（支持 `\|300` 尺寸写法，自动忽略尺寸参数） |
| `> [!note] 标题` | Note Callout |
| `> [!info]` | Info Callout |
| `> [!tip]` | Tip Callout |
| `> [!warning]` | Warning Callout |
| `> [!danger]` | Danger Callout |
| `> [!example]` | Example Callout |
| `> [!quote]` | Quote Callout |
| 标准 Markdown | 标题、列表、表格、代码块、粗体、斜体等全部支持 |
