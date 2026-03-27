import re
import base64
import subprocess
import sys
import tempfile
from pathlib import Path

def find_image(image_name, vault_root):
    """在 vault 里递归搜索图片文件"""
    for p in Path(vault_root).rglob(image_name):
        return p
    return None

def image_to_base64(image_path):
    """图片转 base64 data URI"""
    suffix = image_path.suffix.lower()
    mime = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
    }.get(suffix, 'image/png')
    
    with open(image_path, 'rb') as f:
        data = base64.b64encode(f.read()).decode()
    return f"data:{mime};base64,{data}"

def convert_wiki_images(content, vault_root, log_fn=print):
    """把 ![[图片.png]] 转成内嵌 base64 的标准 Markdown"""
    def replace_image(match):
        image_name = match.group(1).strip()
        # 支持带尺寸的写法，如 ![[img.png|300]]
        image_name = image_name.split('|')[0].strip()

        image_path = find_image(image_name, vault_root)
        if image_path:
            b64 = image_to_base64(image_path)
            return f"![{image_name}]({b64})"
        else:
            log_fn(f"  ⚠️  找不到图片: {image_name}")
            return f"*[图片未找到: {image_name}]*"

    return re.sub(r'!\[\[([^\]]+)\]\]', replace_image, content)

def convert_callouts(content):
    """把 Obsidian callout 转成带样式的 HTML 块"""
    lines = content.split('\n')
    result = []
    i = 0
    
    callout_colors = {
        'note': '#4A90D9',
        'info': '#4A90D9',
        'tip': '#34A853',
        'success': '#34A853',
        'warning': '#F5A623',
        'caution': '#F5A623',
        'danger': '#E53935',
        'error': '#E53935',
        'bug': '#E53935',
        'example': '#9B59B6',
        'quote': '#888888',
        'abstract': '#00BCD4',
        'summary': '#00BCD4',
    }
    
    callout_icons = {
        'note': '📝', 'info': 'ℹ️', 'tip': '💡', 'success': '✅',
        'warning': '⚠️', 'caution': '⚠️', 'danger': '🚨', 'error': '❌',
        'bug': '🐛', 'example': '📌', 'quote': '💬',
        'abstract': '📋', 'summary': '📋',
    }
    
    while i < len(lines):
        line = lines[i]
        # 匹配 callout 开头：> [!type] 可选标题
        callout_match = re.match(r'^>\s*\[!(\w+)\]\s*(.*)', line)
        
        if callout_match:
            callout_type = callout_match.group(1).lower()
            callout_title = callout_match.group(2).strip() or callout_type.capitalize()
            color = callout_colors.get(callout_type, '#888888')
            icon = callout_icons.get(callout_type, '📌')
            
            # 收集 callout 内容行（以 > 开头的连续行）
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].startswith('>'):
                body_lines.append(lines[i][1:].strip())
                i += 1
            
            body = '\n'.join(body_lines)
            
            html_block = f"""
<div style="border-left: 4px solid {color}; background: {color}18; padding: 12px 16px; margin: 12px 0; border-radius: 0 6px 6px 0;">
<strong style="color: {color};">{icon} {callout_title}</strong>
<div style="margin-top: 6px;">{body}</div>
</div>
"""
            result.append(html_block)
        else:
            result.append(line)
            i += 1
    
    return '\n'.join(result)

def md_to_html(md_path, vault_root, output_dir=None, log_fn=print):
    md_path = Path(md_path)
    vault_root = Path(vault_root)
    out_dir = Path(output_dir) if output_dir else md_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / (md_path.stem + '.html')

    log_fn(f"📄 处理文件: {md_path.name}")

    # 读取原始内容
    content = md_path.read_text(encoding='utf-8')

    # 预处理：转换图片
    log_fn("  🖼️  转换 Wiki 图片链接...")
    content = convert_wiki_images(content, vault_root, log_fn)

    # 预处理：转换 callout
    log_fn("  📦 转换 Callout 块...")
    content = convert_callouts(content)

    # 用 Pandoc 转 HTML（临时文件写到系统临时目录）
    log_fn("  ✨ Pandoc 转换中...")
    css_style = """
    <style>
      body { font-family: -apple-system, 'PingFang SC', sans-serif;
             max-width: 860px; margin: 40px auto; padding: 0 20px;
             color: #333; line-height: 1.7; }
      table { border-collapse: collapse; width: 100%; margin: 16px 0; }
      th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
      th { background: #f5f5f5; font-weight: 600; }
      tr:nth-child(even) { background: #fafafa; }
      code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px;
             font-family: 'Fira Code', monospace; font-size: 0.9em; }
      pre { background: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; }
      img { max-width: 100%; height: auto; border-radius: 4px; }
      blockquote { border-left: 3px solid #ddd; margin: 0; padding-left: 16px; color: #666; }
    </style>
    """

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / '_converted.md'
        css_tmp = Path(tmp_dir) / '_style.css'
        tmp_path.write_text(content, encoding='utf-8')
        css_tmp.write_text(css_style, encoding='utf-8')

        result = subprocess.run([
            'pandoc', str(tmp_path),
            '-f', 'markdown+raw_html',
            '-t', 'html5',
            '--standalone',
            '--metadata', f'title={md_path.stem}',
            '--css', str(css_tmp),
            '--embed-resources',
        ], capture_output=True, text=True, encoding='utf-8')

    if result.returncode != 0:
        log_fn(f"  ❌ Pandoc 错误: {result.stderr}")
        return None

    output_path.write_text(result.stdout, encoding='utf-8')
    log_fn(f"  ✅ 输出: {output_path}")
    return output_path

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python obs2feishu.py <markdown文件路径> <vault根目录>")
        print("示例: python obs2feishu.py notes/myfile.md /Users/me/MyVault")
        sys.exit(1)
    
    md_to_html(sys.argv[1], sys.argv[2])