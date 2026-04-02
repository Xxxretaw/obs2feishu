import { Vault, TFile, TFolder } from "obsidian";
import { marked } from "marked";

// ── MIME 类型映射 ──
const MIME_MAP: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};

// ── Callout 配色和图标 ──
const CALLOUT_COLORS: Record<string, string> = {
  note: "#4A90D9",
  info: "#4A90D9",
  tip: "#34A853",
  success: "#34A853",
  warning: "#F5A623",
  caution: "#F5A623",
  danger: "#E53935",
  error: "#E53935",
  bug: "#E53935",
  example: "#9B59B6",
  quote: "#888888",
  abstract: "#00BCD4",
  summary: "#00BCD4",
};

const CALLOUT_ICONS: Record<string, string> = {
  note: "\u{1F4DD}",
  info: "\u2139\uFE0F",
  tip: "\u{1F4A1}",
  success: "\u2705",
  warning: "\u26A0\uFE0F",
  caution: "\u26A0\uFE0F",
  danger: "\u{1F6A8}",
  error: "\u274C",
  bug: "\u{1F41B}",
  example: "\u{1F4CC}",
  quote: "\u{1F4AC}",
  abstract: "\u{1F4CB}",
  summary: "\u{1F4CB}",
};

const CSS_STYLE = `
<style>
  body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
         max-width: 860px; margin: 40px auto; padding: 0 20px;
         color: #333; line-height: 1.7; }
  table { border-collapse: collapse; width: 100%; margin: 16px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; font-weight: 600; }
  tr:nth-child(even) { background: #fafafa; }
  code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px;
         font-family: 'Fira Code', monospace; font-size: 0.9em; }
  pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; }
  pre code { background: none; padding: 0; }
  img { max-width: 100%; height: auto; border-radius: 4px; }
  blockquote { border-left: 3px solid #ddd; margin: 0; padding-left: 16px; color: #666; }
  h1, h2, h3, h4, h5, h6 { margin-top: 1.4em; margin-bottom: 0.6em; }
  a { color: #4A90D9; text-decoration: none; }
  a:hover { text-decoration: underline; }
  hr { border: none; border-top: 1px solid #ddd; margin: 2em 0; }
</style>`;

/**
 * 在 vault 中查找图片文件（递归搜索）
 */
function findImageInVault(vault: Vault, imageName: string): TFile | null {
  const allFiles = vault.getFiles();
  for (const file of allFiles) {
    if (file.name === imageName) {
      return file;
    }
  }
  return null;
}

/**
 * 将图片文件转为 base64 data URI
 */
async function imageToBase64(vault: Vault, file: TFile): Promise<string> {
  const ext = file.extension.toLowerCase();
  const mime = MIME_MAP["." + ext] || "image/png";
  const data = await vault.readBinary(file);
  const base64 = arrayBufferToBase64(data);
  return `data:${mime};base64,${base64}`;
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return window.btoa(binary);
}

/**
 * 将 ![[image.png]] wiki 图片链接转为内嵌 base64
 */
export async function convertWikiImages(
  content: string,
  vault: Vault,
  logFn: (msg: string) => void
): Promise<string> {
  const regex = /!\[\[([^\]]+)\]\]/g;
  const matches = [...content.matchAll(regex)];

  for (const match of matches) {
    const rawName = match[1].trim();
    const imageName = rawName.split("|")[0].trim();

    const imageFile = findImageInVault(vault, imageName);
    if (imageFile) {
      const b64 = await imageToBase64(vault, imageFile);
      content = content.replace(match[0], `![${imageName}](${b64})`);
    } else {
      logFn(`  ⚠️  找不到图片: ${imageName}`);
      content = content.replace(match[0], `*[图片未找到: ${imageName}]*`);
    }
  }

  return content;
}

/**
 * 将 Obsidian callout 语法转为带样式的 HTML 块
 */
export function convertCallouts(content: string): string {
  const lines = content.split("\n");
  const result: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const calloutMatch = line.match(/^>\s*\[!(\w+)\]\s*(.*)/);

    if (calloutMatch) {
      const calloutType = calloutMatch[1].toLowerCase();
      const calloutTitle =
        calloutMatch[2].trim() ||
        calloutType.charAt(0).toUpperCase() + calloutType.slice(1);
      const color = CALLOUT_COLORS[calloutType] || "#888888";
      const icon = CALLOUT_ICONS[calloutType] || "\u{1F4CC}";

      const bodyLines: string[] = [];
      i += 1;
      while (i < lines.length && lines[i].startsWith(">")) {
        bodyLines.push(lines[i].substring(1).trim());
        i += 1;
      }

      const body = bodyLines.join("\n");

      const htmlBlock = `
<div style="border-left: 4px solid ${color}; background: ${color}18; padding: 12px 16px; margin: 12px 0; border-radius: 0 6px 6px 0;">
<strong style="color: ${color};">${icon} ${calloutTitle}</strong>
<div style="margin-top: 6px;">${body}</div>
</div>`;
      result.push(htmlBlock);
    } else {
      result.push(line);
      i += 1;
    }
  }

  return result.join("\n");
}

/**
 * 去除 YAML frontmatter
 */
function stripFrontmatter(content: string): string {
  if (content.startsWith("---")) {
    const endIndex = content.indexOf("---", 3);
    if (endIndex !== -1) {
      return content.substring(endIndex + 3).trimStart();
    }
  }
  return content;
}

/**
 * 将 [[wiki link]] 转为纯文本（飞书 HTML 不支持 wiki link）
 */
function convertWikiLinks(content: string): string {
  // [[link|display]] → display
  content = content.replace(/\[\[([^\]]+)\|([^\]]+)\]\]/g, "$2");
  // [[link]] → link
  content = content.replace(/\[\[([^\]]+)\]\]/g, "$1");
  return content;
}

/**
 * 主转换函数：Markdown → 完整 HTML
 */
export async function mdToHtml(
  file: TFile,
  vault: Vault,
  logFn: (msg: string) => void
): Promise<string> {
  logFn(`📄 处理文件: ${file.name}`);

  let content = await vault.read(file);

  // 去除 frontmatter
  content = stripFrontmatter(content);

  // 预处理：转换 wiki 图片链接
  logFn("  🖼️  转换 Wiki 图片链接...");
  content = await convertWikiImages(content, vault, logFn);

  // 预处理：转换 wiki 链接
  content = convertWikiLinks(content);

  // 预处理：转换 callout
  logFn("  📦 转换 Callout 块...");
  content = convertCallouts(content);

  // 用 marked 转 HTML
  logFn("  ✨ 转换 HTML 中...");
  const htmlBody = await marked(content, {
    breaks: true,
    gfm: true,
  });

  const title = file.basename;
  const fullHtml = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title}</title>
${CSS_STYLE}
</head>
<body>
${htmlBody}
</body>
</html>`;

  return fullHtml;
}
