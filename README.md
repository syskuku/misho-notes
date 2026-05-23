# ✿ Misho Notes

A lightweight, self-hosted Markdown notebook with a Japanese wabi-sabi aesthetic.

未書 — the beauty of what remains unwritten.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **Markdown Editor** — Live preview with syntax highlighting (Highlight.js)
- **Math Formulas** — LaTeX rendering via KaTeX (`$inline$` / `$$block$$`)
- **Sections & Tags** — Organize notes with custom icons, colors, and tags
- **Share Links** — Generate public links for individual notes (single-page HTML, no login required)
- **Print View** — Serif typography (Noto Serif SC) optimized for printing
- **Responsive** — Full mobile support with slide-out sidebar
- **File Storage** — Notes stored as `.md` + `.meta.json`, easy to backup and migrate

## Quick Start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/misho-notes.git
cd misho-notes

# Install
pip install -r requirements.txt

# Run
python app.py
```

Open `http://localhost:1145`, default password is `changeme`.

## Configuration

All via environment variables:

```bash
MISHO_PASSWORD=your_password    # Login password (default: changeme)
MISHO_PORT=8080                 # Port (default: 1145)
MISHO_DATA_DIR=/path/to/data    # Data directory (default: ./data)
```

## Project Structure

```
misho-notes/
├── app.py              # Flask backend
├── requirements.txt
├── .gitignore
├── static/
│   └── index.html      # Single-file frontend (HTML + CSS + JS)
└── data/               # Created at runtime
    ├── sections.json
    ├── shares.json
    └── {section_id}/
        ├── {note_id}.md
        └── {note_id}.meta.json
```

## Tech Stack

- **Backend** — Flask, Python-Markdown
- **Frontend** — Vanilla JS (no framework), Marked.js, Highlight.js, KaTeX
- **Fonts** — Noto Serif SC, Noto Sans SC
- **Design** — Wabi-sabi aesthetic: parchment tones, ink accents, serif typography

## Deployment

### Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:1145 app:app
```

### Nginx

```nginx
server {
    listen 80;
    server_name notes.example.com;

    location / {
        proxy_pass http://127.0.0.1:1145;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## License

MIT
