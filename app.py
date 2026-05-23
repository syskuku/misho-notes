from flask import Flask, request, session, redirect, url_for, jsonify, abort, send_from_directory
from flask_cors import CORS
import json, os, hashlib, secrets, re, time
try:
    import markdown as md_lib
except ImportError:
    md_lib = None
from datetime import datetime
from functools import wraps

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = secrets.token_hex(32)
CORS(app)

DATA_DIR = os.environ.get('MISHO_DATA_DIR', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
SECTIONS_FILE = os.path.join(DATA_DIR, 'sections.json')
SHARE_FILE = os.path.join(DATA_DIR, 'shares.json')
DEFAULT_PASSWORD = os.environ.get('MISHO_PASSWORD', 'changeme')
PASSWORD_HASH = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest()

# ---- Helpers ----

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def load_sections():
    ensure_data_dir()
    if os.path.exists(SECTIONS_FILE):
        with open(SECTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_sections(sections):
    with open(SECTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

def get_note_path(section_id, note_id, ext='.meta.json'):
    return os.path.join(DATA_DIR, section_id, f'{note_id}{ext}')

def load_note_meta(section_id, note_id):
    path = get_note_path(section_id, note_id, '.meta.json')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_note_content(section_id, note_id):
    path = get_note_path(section_id, note_id, '.md')
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

def load_note(section_id, note_id):
    meta = load_note_meta(section_id, note_id)
    if meta:
        content = load_note_content(section_id, note_id)
        meta['content'] = content
        return meta
    return None

def save_note(section_id, note_id, data):
    dir_path = os.path.join(DATA_DIR, section_id)
    os.makedirs(dir_path, exist_ok=True)
    
    md_path = os.path.join(dir_path, f'{note_id}.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(data.get('content', ''))
    
    meta = {k: v for k, v in data.items() if k != 'content'}
    meta_path = os.path.join(dir_path, f'{note_id}.meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def delete_note_file(section_id, note_id):
    md_path = get_note_path(section_id, note_id, '.md')
    meta_path = get_note_path(section_id, note_id, '.meta.json')
    if os.path.exists(md_path):
        os.remove(md_path)
    if os.path.exists(meta_path):
        os.remove(meta_path)

def sanitize(text):
    if not text:
        return ''
    return re.sub(r'<script[^>]*>.*?</script>', '', str(text), flags=re.IGNORECASE | re.DOTALL)

# ---- Share helpers ----

def load_shares():
    ensure_data_dir()
    if os.path.exists(SHARE_FILE):
        with open(SHARE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_shares(shares):
    with open(SHARE_FILE, 'w', encoding='utf-8') as f:
        json.dump(shares, f, ensure_ascii=False, indent=2)

def render_markdown(text):
    if md_lib:
        return md_lib.markdown(text, extensions=["fenced_code", "tables", "codehilite", "toc", "nl2br"])
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paras = safe.split(chr(10)+chr(10))
    return "".join("<p>" + p.replace(chr(10), "<br/>") + "</p>" for p in paras if p.strip())

# ---- Auth ----

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    try:
        pwd = request.json.get('password', '') if request.is_json else ''
        if hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH:
            session['logged_in'] = True
            session.permanent = True
            return jsonify({'ok': True})
        return jsonify({'error': '密码错误'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/check', methods=['GET'])
def check():
    return jsonify({'logged_in': session.get('logged_in', False)})

# ---- Sections API ----

@app.route('/api/sections', methods=['GET'])
@login_required
def get_sections():
    sections = load_sections()
    result = []
    for sid, s in sections.items():
        dir_path = os.path.join(DATA_DIR, sid)
        count = 0
        if os.path.exists(dir_path):
            count = len([f for f in os.listdir(dir_path) if f.endswith('.meta.json')])
        result.append({
            'id': sid, 'name': s.get('name', '未命名'),
            'color': s.get('color', '#4a90d9'),
            'icon': s.get('icon', '📁'),
            'created': s.get('created', ''),
            'count': count
        })
    return jsonify(result)

@app.route('/api/sections', methods=['POST'])
@login_required
def create_section():
    data = request.json
    sid = secrets.token_hex(8)
    sections = load_sections()
    sections[sid] = {
        'name': sanitize(data.get('name', '新分区')),
        'color': data.get('color', '#4a90d9'),
        'icon': data.get('icon', '📁'),
        'created': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    save_sections(sections)
    return jsonify({'id': sid, **sections[sid]})

@app.route('/api/sections/<sid>', methods=['PUT'])
@login_required
def update_section(sid):
    sections = load_sections()
    if sid not in sections:
        return jsonify({'error': '分区不存在'}), 404
    data = request.json
    for k in ('name', 'color', 'icon'):
        if k in data:
            sections[sid][k] = sanitize(data[k]) if k == 'name' else data[k]
    save_sections(sections)
    return jsonify({'ok': True})

@app.route('/api/sections/<sid>', methods=['DELETE'])
@login_required
def delete_section(sid):
    sections = load_sections()
    if sid not in sections:
        return jsonify({'error': '分区不存在'}), 404
    del sections[sid]
    save_sections(sections)
    dir_path = os.path.join(DATA_DIR, sid)
    import shutil
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    return jsonify({'ok': True})

# ---- Notes API ----

@app.route('/api/sections/<sid>/notes', methods=['GET'])
@login_required
def get_notes(sid):
    dir_path = os.path.join(DATA_DIR, sid)
    notes = []
    if os.path.exists(dir_path):
        for f in sorted(os.listdir(dir_path), reverse=True):
            if f.endswith('.meta.json'):
                note_id = f[:-10]
                meta = load_note_meta(sid, note_id)
                if meta:
                    content = load_note_content(sid, note_id)
                    notes.append({
                        'id': note_id,
                        'title': meta.get('title', '无标题'),
                        'updated': meta.get('updated', ''),
                        'tags': meta.get('tags', []),
                        'preview': content[:120].replace('\n', ' ').replace('#', '').strip()
                    })
    return jsonify(notes)

@app.route('/api/sections/<sid>/notes', methods=['POST'])
@login_required
def create_note(sid):
    data = request.json
    nid = secrets.token_hex(8)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    note = {
        'id': nid,
        'title': sanitize(data.get('title', '无标题')),
        'content': data.get('content', ''),
        'tags': data.get('tags', []),
        'created': now,
        'updated': now
    }
    save_note(sid, nid, note)
    return jsonify(note)

@app.route('/api/sections/<sid>/notes/<nid>', methods=['GET'])
@login_required
def get_note(sid, nid):
    note = load_note(sid, nid)
    if not note:
        return jsonify({'error': '笔记不存在'}), 404
    return jsonify(note)

@app.route('/api/sections/<sid>/notes/<nid>', methods=['PUT'])
@login_required
def update_note(sid, nid):
    note = load_note(sid, nid)
    if not note:
        return jsonify({'error': '笔记不存在'}), 404
    data = request.json
    for k in ('title', 'content', 'tags'):
        if k in data:
            note[k] = sanitize(data[k]) if k == 'title' else data[k]
    note['updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    save_note(sid, nid, note)
    return jsonify(note)

@app.route('/api/sections/<sid>/notes/<nid>', methods=['DELETE'])
@login_required
def delete_note(sid, nid):
    delete_note_file(sid, nid)
    return jsonify({'ok': True})

# ---- Share API ----

@app.route('/api/sections/<sid>/notes/<nid>/share', methods=['POST'])
@login_required
def create_share(sid, nid):
    note = load_note(sid, nid)
    if not note:
        return jsonify({'error': '笔记不存在'}), 404
    sections = load_sections()
    section_name = sections.get(sid, {}).get('name', '未知分区')
    shares = load_shares()
    token = secrets.token_urlsafe(16)
    shares[token] = {
        'section_id': sid, 'section_name': section_name,
        'note_id': nid, 'note_title': note.get('title', '无标题'),
        'created': datetime.now().strftime('%Y-%m-%d %H:%M')
    }
    save_shares(shares)
    return jsonify({'ok': True, 'token': token, 'url': f'/s/{token}'})

@app.route('/api/sections/<sid>/notes/<nid>/unshare', methods=['POST'])
@login_required
def unshare_note(sid, nid):
    shares = load_shares()
    to_rm = [t for t, v in shares.items() if v.get('note_id') == nid and v.get('section_id') == sid]
    for t in to_rm:
        del shares[t]
    save_shares(shares)
    return jsonify({'ok': True, 'removed': len(to_rm)})

@app.route('/s/<token>')
def view_shared_note(token):
    shares = load_shares()
    share = shares.get(token)
    if not share:
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>链接已失效</title></head><body style="display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:serif;color:#444"><div style="text-align:center"><h1 style="font-size:4em;color:#bbb;margin-bottom:.2em">🍃</h1><p style="font-size:1.2em">此分享链接已失效</p></div></body></html>', 404
    note = load_note(share['section_id'], share['note_id'])
    if not note:
        return '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>笔记已删除</title></head><body style="display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:serif;color:#444"><div style="text-align:center"><h1 style="font-size:4em;color:#bbb;margin-bottom:.2em">🍂</h1><p style="font-size:1.2em">此笔记已被删除</p></div></body></html>', 404
    html_content = render_markdown(note.get('content', ''))
    title = note.get('title', '无标题')
    section_name = share.get('section_name', '')
    tags = note.get('tags', [])
    tags_html = ('<div class="tags">' + '　·　'.join(f'<span class="tag">{t}</span>' for t in tags) + '</div>') if tags else ''
    updated = note.get('updated', note.get('created', ''))
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} — Syskuku Notebook</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:"Noto Serif SC","Songti SC",serif;background:#faf8f5;color:#2c2c2c;-webkit-font-smoothing:antialiased}}
.page{{max-width:720px;margin:0 auto;padding:60px 48px 80px}}
@media(max-width:640px){{.page{{padding:32px 20px 48px}}}}
.meta-bar{{text-align:center;margin-bottom:48px;opacity:0;animation:fadeIn .8s .2s forwards}}
.meta-bar .section-label{{font-family:"Noto Sans SC",sans-serif;font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#a09080;margin-bottom:16px}}
.meta-bar h1{{font-size:clamp(1.8em,4vw,2.4em);font-weight:700;color:#2c2c2c;line-height:1.4;margin-bottom:12px}}
.meta-bar .date{{font-family:"Noto Sans SC",sans-serif;font-size:12px;color:#b0a090;letter-spacing:1px}}
.ink-divider{{width:60px;height:2px;background:linear-gradient(90deg,transparent,#8a7a6a,transparent);margin:40px auto;opacity:0;animation:fadeIn .8s .4s forwards}}
.tags{{text-align:center;margin-bottom:12px;opacity:0;animation:fadeIn .8s .6s forwards}}
.tags .tag{{font-family:"Noto Sans SC",sans-serif;font-size:11px;color:#a09080;padding:2px 10px;border:1px solid #e0d8d0;border-radius:3px;margin:0 3px;letter-spacing:1px}}
.article{{font-size:16px;line-height:2;color:#3c3c3c;opacity:0;animation:fadeIn .8s .5s forwards}}
.article h1{{font-size:1.6em;font-weight:700;margin:2em 0 .8em;padding-bottom:8px;border-bottom:1px solid #e0d8d0}}
.article h2{{font-size:1.3em;font-weight:600;margin:1.8em 0 .6em;padding-left:12px;border-left:3px solid #c0b0a0}}
.article h3{{font-size:1.1em;font-weight:600;margin:1.5em 0 .5em}}
.article p{{margin:1em 0;text-indent:2em}}
.article p:has(img){{text-indent:0;text-align:center}}
.article img{{max-width:100%;border-radius:4px;margin:16px 0;border:1px solid #e8e0d8}}
.article code{{font-family:"Fira Code",Consolas,monospace;background:#f5f0ea;padding:2px 6px;border-radius:3px;font-size:.9em;color:#6a5a4a}}
.article pre{{background:#2c2c2c;color:#e8e0d8;border-radius:6px;padding:20px;margin:20px 0;overflow-x:auto;font-size:13px;line-height:1.7}}
.article pre code{{background:none;color:inherit;padding:0}}
.article blockquote{{border-left:3px solid #c0b0a0;padding:12px 20px;margin:20px 0;color:#6a6a6a;background:#f8f4ef;border-radius:0 4px 4px 0;font-style:italic}}
.article blockquote p{{text-indent:0}}
.article table{{border-collapse:collapse;width:100%;margin:20px 0;font-size:14px}}
.article th{{background:#f0ebe5;border-bottom:2px solid #c0b0a0;padding:10px 14px;text-align:left;font-weight:600}}
.article td{{border-bottom:1px solid #e8e0d8;padding:10px 14px}}
.article hr{{border:none;height:1px;background:#d0c8c0;margin:2em auto;width:80%}}
.article ul,.article ol{{padding-left:28px;margin:1em 0}}
.article li{{margin:.5em 0}}
.article a{{color:#7a6a5a;border-bottom:1px solid #c0b0a0;text-decoration:none;transition:.2s}}
.article a:hover{{color:#5a4a3a;border-bottom-color:#8a7a6a}}
.footer{{text-align:center;margin-top:60px;padding-top:32px;border-top:1px solid #e0d8d0;font-family:"Noto Sans SC",sans-serif;font-size:11px;color:#b0a090;letter-spacing:1px;opacity:0;animation:fadeIn .8s .8s forwards}}
.footer .logo{{font-size:20px;margin-bottom:8px;opacity:.4}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
@media print{{body{{background:#fff}}.page{{padding:40px 32px}}.meta-bar,.ink-divider,.tags,.article,.footer{{opacity:1!important;animation:none!important;transform:none!important}}}}
</style>
</head>
<body>
<div class="page">
  <div class="meta-bar">
    <div class="section-label">{section_name}</div>
    <h1>{title}</h1>
    <div class="date">{updated}</div>
  </div>
  <div class="ink-divider"></div>
  {tags_html}
  <div class="article">{html_content}</div>
  <div class="footer"><div class="logo">✿</div><div>Syskuku's Notebook</div></div>
</div>
<script>document.addEventListener("DOMContentLoaded",function(){{renderMathInElement(document.querySelector(".article"),{{delimiters:[{{left:"$$",right:"$$",display:true}},{{left:"$",right:"$",display:false}},{{left:"\\[",right:"\\]",display:true}},{{left:"\\(",right:"\\)",display:false}}],throwOnError:false}})}})</script>
</body>
</html>'''

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# 性能监控
@app.after_request
def add_header(response):
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response

if __name__ == '__main__':
    # 使用多线程处理并发请求
    port = int(os.environ.get('MISHO_PORT', 1145))
    print(f"\n  ✿ Misho Notes 启动成功")
    print(f"     http://localhost:{port}")
    print(f"     默认密码: {DEFAULT_PASSWORD}\n")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
