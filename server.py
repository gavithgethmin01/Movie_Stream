import os
from flask import Flask, request, abort, Response
from urllib.parse import quote
from pathlib import Path

app = Flask(__name__)

# ================= CONFIG =================
MOVIES_ROOT = r"D:\Movies"  # ← change if needed (use raw string for Windows paths)
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
        import re
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
                clean_file = clean_name(item.stem) + item.suffix
                tree['children'].append({
                    'name': clean_file,
                    'path': str(item.relative_to(base)),
                    'is_dir': False
                })
    except PermissionError:
        pass

    return tree


@app.route('/', defaults={'req_path': ''})
@app.route('/<path:req_path>')
def browse(req_path):
    base_path = Path(MOVIES_ROOT)
    current_path = (base_path / req_path).resolve()

    # Security: prevent path traversal
    if not current_path.is_relative_to(base_path):
        abort(403)

    if not current_path.exists():
        abort(404)

    if current_path.is_file():
        # Direct file access → redirect to player
        from flask import redirect, url_for
        return redirect(url_for('play', file_path=req_path))

    # Build tree
    tree = get_tree(current_path, base_path)

    parent = None
    if req_path:
        parent_parts = Path(req_path).parts[:-1]
        parent = '/'.join(parent_parts) if parent_parts else ''

    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Movie Library - {clean_name(current_path.name) or 'Home'}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                padding: 20px;
                position: relative;
                overflow-x: hidden;
            }}
            
            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at 20% 50%, rgba(255,255,255,0.05) 0%, transparent 50%),
                            radial-gradient(circle at 80% 80%, rgba(255,255,255,0.05) 0%, transparent 50%);
                pointer-events: none;
                z-index: 0;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                position: relative;
                z-index: 1;
            }}
            
            header {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            
            h1 {{
                color: #fff;
                text-align: center;
                font-size: 2.5rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
                margin-bottom: 10px;
            }}
            
            .subtitle {{
                text-align: center;
                color: rgba(255, 255, 255, 0.8);
                font-size: 1rem;
            }}
            
            .breadcrumb {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 15px 20px;
                margin-bottom: 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                flex-wrap: wrap;
                gap: 8px;
            }}
            
            .breadcrumb a {{
                color: #fff;
                text-decoration: none;
                padding: 5px 12px;
                border-radius: 8px;
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.1);
                font-weight: 500;
            }}
            
            .breadcrumb a:hover {{
                background: rgba(255, 255, 255, 0.25);
                transform: translateY(-2px);
            }}
            
            .breadcrumb-sep {{
                color: rgba(255, 255, 255, 0.5);
            }}
            
            .content-card {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 25px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            
            ul {{
                list-style: none;
            }}
            
            li {{
                margin: 8px 0;
            }}
            
            .item-link {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 15px 20px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                text-decoration: none;
                color: #fff;
                transition: all 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.1);
                font-weight: 500;
            }}
            
            .item-link:hover {{
                background: rgba(255, 255, 255, 0.2);
                transform: translateX(8px);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }}
            
            .item-icon {{
                font-size: 1.5rem;
                flex-shrink: 0;
            }}
            
            .item-name {{
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}
            
            .up-link {{
                background: rgba(248, 81, 73, 0.2);
                border-color: rgba(248, 81, 73, 0.3);
            }}
            
            .up-link:hover {{
                background: rgba(248, 81, 73, 0.3);
            }}
            
            .folder-link {{
                background: rgba(240, 136, 62, 0.15);
            }}
            
            .folder-link:hover {{
                background: rgba(240, 136, 62, 0.25);
            }}
            
            .file-link {{
                background: rgba(88, 166, 255, 0.15);
            }}
            
            .file-link:hover {{
                background: rgba(88, 166, 255, 0.25);
            }}
            
            @media (max-width: 768px) {{
                body {{
                    padding: 10px;
                }}
                
                h1 {{
                    font-size: 1.8rem;
                }}
                
                header {{
                    padding: 20px;
                }}
                
                .breadcrumb {{
                    padding: 12px 15px;
                    font-size: 0.9rem;
                }}
                
                .item-link {{
                    padding: 12px 15px;
                }}
                
                .item-icon {{
                    font-size: 1.3rem;
                }}
            }}
            
            @media (max-width: 480px) {{
                h1 {{
                    font-size: 1.5rem;
                }}
                
                .subtitle {{
                    font-size: 0.85rem;
                }}
                
                .item-name {{
                    font-size: 0.9rem;
                }}
            }}
        </style>
    </head>
    <body>
    <div class="container">
        <header>
            <h1>🎬 Movie Library</h1>
            <div class="subtitle">Your personal cinema collection</div>
        </header>

        <div class="breadcrumb">
            <a href="/">🏠 Home</a>
            {render_breadcrumb(req_path)}
        </div>

        <div class="content-card">
            <ul>
                {render_up_link(parent)}
                {render_tree_items(tree["children"], req_path)}
            </ul>
        </div>
    </div>
    </body>
    </html>
    '''
    return html


def render_breadcrumb(req_path):
    if not req_path:
        return ''
    parts = Path(req_path).parts
    crumbs = []
    for i, p in enumerate(parts):
        path = '/'.join(parts[:i+1])
        crumbs.append(f'<span class="breadcrumb-sep">/</span><a href="/{quote(path)}">{clean_name(p)}</a>')
    return ''.join(crumbs)


def render_up_link(parent):
    if parent is None:
        return ''
    url = quote(parent) if parent else ''
    return f'<li><a href="/{url}" class="item-link up-link"><span class="item-icon">↑</span><span class="item-name">Up one level</span></a></li>'


def render_tree_items(items, current_path):
    html = ""
    for item in items:
        if item['is_dir']:
            url = quote(item['path']) if item['path'] else ''
            html += f'<li><a href="/{url}" class="item-link folder-link"><span class="item-icon">📁</span><span class="item-name">{item["name"]}</span></a></li>'
        else:
            from flask import url_for
            play_url = url_for('play', file_path=item['path'])
            html += f'<li><a href="{play_url}" class="item-link file-link"><span class="item-icon">🎥</span><span class="item-name">{item["name"]}</span></a></li>'
    return html


@app.route('/play/<path:file_path>')
def play(file_path):
    safe_path = (Path(MOVIES_ROOT) / file_path).resolve()
    if not safe_path.is_file() or not safe_path.is_relative_to(MOVIES_ROOT):
        abort(404)

    name = clean_name(safe_path.stem)
    from flask import url_for

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Playing: {name}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                background: #000;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                overflow: hidden;
            }}
            
            .player-container {{
                position: relative;
                width: 100vw;
                height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                background: #000;
            }}
            
            .title-bar {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                padding: 20px;
                background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
                z-index: 100;
                display: flex;
                justify-content: space-between;
                align-items: center;
                opacity: 1;
                transition: opacity 0.3s ease;
            }}
            
            .player-container:hover .title-bar {{
                opacity: 1;
            }}
            
            .title-bar.hidden {{
                opacity: 0;
            }}
            
            h1 {{
                color: #fff;
                font-size: 1.3rem;
                font-weight: 600;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                flex: 1;
            }}
            
            .back-btn {{
                background: rgba(255, 255, 255, 0.2);
                color: #fff;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                font-size: 1rem;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                backdrop-filter: blur(10px);
            }}
            
            .back-btn:hover {{
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }}
            
            video {{
                max-width: 100%;
                max-height: 100%;
                width: 100%;
                height: 100%;
                object-fit: contain;
            }}
            
            @media (max-width: 768px) {{
                h1 {{
                    font-size: 1rem;
                }}
                
                .back-btn {{
                    padding: 8px 16px;
                    font-size: 0.9rem;
                }}
                
                .title-bar {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="player-container">
            <div class="title-bar" id="titleBar">
                <h1>🎬 {name}</h1>
                <a href="javascript:history.back()" class="back-btn">← Back</a>
            </div>
            <video id="videoPlayer" controls autoplay>
                <source src="{url_for('stream', file_path=file_path)}" type="video/mp4">
                Your browser does not support video playback.
            </video>
        </div>
        
        <script>
            const video = document.getElementById('videoPlayer');
            const titleBar = document.getElementById('titleBar');
            let hideTimeout;
            
            function showControls() {{
                titleBar.classList.remove('hidden');
                clearTimeout(hideTimeout);
                hideTimeout = setTimeout(() => {{
                    if (!video.paused) {{
                        titleBar.classList.add('hidden');
                    }}
                }}, 3000);
            }}
            
            document.addEventListener('mousemove', showControls);
            document.addEventListener('touchstart', showControls);
            
            video.addEventListener('play', () => {{
                hideTimeout = setTimeout(() => {{
                    titleBar.classList.add('hidden');
                }}, 3000);
            }});
            
            video.addEventListener('pause', () => {{
                titleBar.classList.remove('hidden');
                clearTimeout(hideTimeout);
            }});
        </script>
    </body>
    </html>
    '''


@app.route('/stream/<path:file_path>')
def stream(file_path):
    """Stream video with proper range support for seeking"""
    full_path = (Path(MOVIES_ROOT) / file_path).resolve()

    if not full_path.is_file() or not full_path.is_relative_to(MOVIES_ROOT):
        abort(404)

    # Get file size
    file_size = full_path.stat().st_size
    
    # Handle range request
    range_header = request.headers.get('Range')
    
    if not range_header:
        # No range requested, send entire file
        return Response(
            open(full_path, 'rb'),
            mimetype='video/mp4',
            headers={
                'Content-Length': str(file_size),
                'Accept-Ranges': 'bytes'
            }
        )
    
    # Parse range header
    byte_range = range_header.replace('bytes=', '').split('-')
    start = int(byte_range[0]) if byte_range[0] else 0
    end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1
    
    # Ensure valid range
    if start >= file_size or end >= file_size:
        abort(416)  # Range Not Satisfiable
    
    length = end - start + 1
    
    # Read the requested chunk
    def generate():
        with open(full_path, 'rb') as f:
            f.seek(start)
            remaining = length
            chunk_size = 8192
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data
    
    response = Response(
        generate(),
        status=206,  # Partial Content
        mimetype='video/mp4',
        direct_passthrough=True
    )
    
    response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
    response.headers.add('Content-Length', str(length))
    response.headers.add('Accept-Ranges', 'bytes')
    
    return response


if __name__ == "__main__":
    print(f"Movie root: {MOVIES_ROOT}")
    print(f"Running at: http://localhost:5000  (or your network IP:5000)")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)