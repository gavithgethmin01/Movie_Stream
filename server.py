import os
import re
from flask import Flask, request, abort, Response, redirect, url_for
from urllib.parse import quote
from pathlib import Path

app = Flask(__name__)

# ================= CONFIG =================
# Change this to your actual movie folder path
MOVIES_ROOT = r"D:\Movies"  
ALLOWED_EXT = {'.mp4', '.mkv', '.avi', '.webm', '.mov'}
# ===========================================

def clean_name(name: str) -> str:
    """Remove common release tags from folder/file names"""
    tags = [
        r'\[.*?\]', r'\(.*?\)', r'\{.*?\}', 'YTS', 'YIFY', 'BluRay', 'WEBRip',
        'x264', 'x265', '10bit', '5.1', 'REPACK', 'EXTENDED', 'REMUX', 'REMUSTERED'
    ]
    clean = name
    for tag in tags:
        clean = re.sub(tag, '', clean, flags=re.IGNORECASE)
    return clean.strip(' .-_[]()').replace('.', ' ').strip()

def get_tree(path: Path, base: Path):
    """Build folder tree structure for template"""
    rel = path.relative_to(base)
    tree = {
        'name': clean_name(path.name) or path.name,
        'path': str(rel) if str(rel) != '.' else '',
        'is_dir': True,
        'children': []
    }
    try:
        items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        for item in items:
            if item.is_dir():
                tree['children'].append(get_tree(item, base))
            elif item.suffix.lower() in ALLOWED_EXT:
                clean_file = clean_name(item.stem)
                tree['children'].append({
                    'name': clean_file,
                    'path': str(item.relative_to(base)),
                    'is_dir': False
                })
    except PermissionError:
        pass
    return tree

def render_breadcrumb(req_path):
    if not req_path:
        return ''
    parts = Path(req_path).parts
    crumbs = []
    for i, p in enumerate(parts):
        path = '/'.join(parts[:i+1])
        crumbs.append(f'<span style="margin: 0 8px; opacity: 0.6;">/</span><a href="/{quote(path)}">{clean_name(p)}</a>')
    return ''.join(crumbs)

def render_up_link(parent):
    if parent is None:
        return ''
    url = quote(parent) if parent else ''
    return f'''
        <a href="/{url}" class="item-card back-card">
            <div class="item-icon">🔙</div>
            <div class="item-name">Go Back</div>
        </a>
    '''

def render_tree_items(items):
    html = ""
    for item in items:
        if item['is_dir']:
            url = quote(item['path'])
            icon = "📂"
            link = f'/{url}'
        else:
            link = url_for('play', file_path=item['path'])
            icon = "🎞️"
        
        html += f'''
            <a href="{link}" class="item-card">
                <div class="item-icon">{icon}</div>
                <div class="item-name">{item["name"]}</div>
            </a>
        '''
    return html

@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def browse(req_path):
    base_path = Path(MOVIES_ROOT)
    current_path = (base_path / req_path).resolve()

    if not current_path.is_relative_to(base_path):
        abort(403)
    if not current_path.exists():
        abort(404)
    if current_path.is_file():
        return redirect(url_for('play', file_path=req_path))

    tree = get_tree(current_path, base_path)
    parent = None
    if req_path:
        parent_parts = Path(req_path).parts[:-1]
        parent = '/'.join(parent_parts) if parent_parts else ''

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Movie Library - {clean_name(current_path.name) or 'Home'}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            
            body {{
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #f093fb 100%);
                min-height: 100vh;
                font-family: 'Segoe UI', Roboto, Helvetica, sans-serif;
                padding: 40px 20px;
                color: white;
            }}
            
            .header-section {{
                text-align: center;
                margin-bottom: 40px;
            }}

            .header-title {{
                font-size: 3rem;
                margin-bottom: 10px;
                text-shadow: 2px 4px 8px rgba(0,0,0,0.2);
            }}

            .breadcrumb {{
                max-width: 1200px;
                margin: 0 auto 30px auto;
                background: rgba(255, 255, 255, 0.15);
                padding: 12px 25px;
                border-radius: 50px;
                backdrop-filter: blur(10px);
                display: inline-block;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}

            .breadcrumb a {{ color: white; text-decoration: none; font-weight: 600; }}
            .breadcrumb a:hover {{ text-decoration: underline; }}

            .grid-container {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 25px;
                max-width: 1200px;
                margin: 0 auto;
            }}

            .item-card {{
                background: rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(15px);
                border-radius: 24px;
                padding: 25px;
                text-align: center;
                text-decoration: none;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: 1px solid rgba(255, 255, 255, 0.4);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                aspect-ratio: 1 / 1;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
            }}

            .item-card:hover {{
                transform: translateY(-12px) scale(1.02);
                background: rgba(255, 255, 255, 0.35);
                box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            }}

            .item-icon {{
                font-size: 4.5rem;
                margin-bottom: 15px;
                filter: drop-shadow(0 8px 4px rgba(0,0,0,0.1));
            }}

            .item-name {{
                color: white;
                font-weight: 700;
                font-size: 1.1rem;
                line-height: 1.3;
                text-shadow: 1px 2px 4px rgba(0,0,0,0.2);
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }}

            .back-card {{ background: rgba(0, 0, 0, 0.1); }}

            @media (max-width: 600px) {{
                .grid-container {{ grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }}
                .header-title {{ font-size: 2rem; }}
            }}
        </style>
    </head>
    <body>
        <div class="header-section">
            <h1 class="header-title">🎬 Movie Library</h1>
            <div class="breadcrumb">
                <a href="/">🏠 Home</a> {render_breadcrumb(req_path)}
            </div>
        </div>

        <div class="grid-container">
            {render_up_link(parent)}
            {render_tree_items(tree["children"])}
        </div>
    </body>
    </html>
    '''

@app.route('/play/<path:file_path>')
def play(file_path):
    safe_path = (Path(MOVIES_ROOT) / file_path).resolve()
    if not safe_path.is_file() or not safe_path.is_relative_to(MOVIES_ROOT):
        abort(404)

    name = clean_name(safe_path.stem)
    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" /><title>Playing: {name}</title>
        <style>
            body {{ background: #000; margin: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; font-family: sans-serif; }}
            .container {{ width: 100%; height: 100%; position: relative; }}
            video {{ width: 100%; height: 100%; object-fit: contain; }}
            .back-btn {{ position: absolute; top: 20px; left: 20px; z-index: 10; padding: 10px 20px; background: rgba(255,255,255,0.2); color: white; text-decoration: none; border-radius: 5px; backdrop-filter: blur(5px); }}
        </style>
    </head>
    <body>
        <div class="container">
            <a href="javascript:history.back()" class="back-btn">← Back</a>
            <video controls autoplay>
                <source src="{url_for('stream', file_path=file_path)}" type="video/mp4">
            </video>
        </div>
    </body>
    </html>
    '''

@app.route('/stream/<path:file_path>')
def stream(file_path):
    full_path = (Path(MOVIES_ROOT) / file_path).resolve()
    if not full_path.is_file() or not full_path.is_relative_to(MOVIES_ROOT):
        abort(404)

    file_size = full_path.stat().st_size
    range_header = request.headers.get('Range')
    
    if not range_header:
        return Response(open(full_path, 'rb'), mimetype='video/mp4', headers={'Content-Length': str(file_size), 'Accept-Ranges': 'bytes'})
    
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0])
    end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
    length = end - start + 1
    
    def generate():
        with open(full_path, 'rb') as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(8192, remaining))
                if not chunk: break
                remaining -= len(chunk)
                yield chunk
    
    res = Response(generate(), status=206, mimetype='video/mp4', direct_passthrough=True)
    res.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    res.headers.add('Content-Length', str(length))
    res.headers.add('Accept-Ranges', 'bytes')
    return res

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
