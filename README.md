# obs2feishu

Obsidian 插件：将 Markdown 笔记导出为飞书兼容的 HTML 文件。

## 功能

- **Wiki 图片内嵌**：自动将 `![[图片.png]]` 转为 Base64 内嵌，HTML 无需额外携带图片
- **Callout 转换**：`> [!note]`、`> [!warning]` 等 Callout 块转为带样式的 HTML
- **Wiki Link 处理**：`[[链接]]` 自动转为纯文本
- **Frontmatter 去除**：YAML 头信息不会出现在 HTML 中
- **零外部依赖**：使用 marked 库转换，无需安装 Pandoc

## 安装

1. 在 vault 目录下创建 `.obsidian/plugins/obs2feishu/`
2. 将 `main.js`、`manifest.json`、`styles.css` 复制到该目录
3. Obsidian 设置 → 第三方插件 → 启用 Obs2Feishu

## 使用

- 打开任意 `.md` 文件，点击右上角 **⋮ 更多选项** → **导出为飞书 HTML**
- 或使用命令面板 `Ctrl+P` → 搜索「导出当前文件为飞书 HTML」

HTML 文件会生成在 Markdown 同目录下，并自动用浏览器打开。

## 开发

```bash
npm install
npm run dev    # 开发构建
npm run build  # 生产构建
```

## 支持的 Obsidian 语法

| 语法 | 说明 |
|------|------|
| `![[image.png]]` | Wiki 图片嵌入（支持 `\|300` 尺寸写法） |
| `[[链接]]` / `[[链接\|显示文本]]` | Wiki Link → 纯文本 |
| `> [!note]` `> [!warning]` 等 | Callout 块（支持 13 种类型） |
| 标准 Markdown | 标题、列表、表格、代码块等全部支持 |
