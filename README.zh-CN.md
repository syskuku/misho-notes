# ✿ Misho Notes

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

轻量级自托管 Markdown 笔记本，日式侘寂美学风格。

未書 — 未书写之美的所在。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 特性

- **Markdown 编辑器** — 实时预览，代码高亮（Highlight.js）
- **数学公式** — KaTeX 渲染 LaTeX（`$行内$` / `$$独立块$$`）
- **分区与标签** — 自定义图标、颜色分区，标签分类管理
- **分享链接** — 生成公开链接，单页 HTML 展示，无需登录
- **打印排版** — Noto Serif SC 衬线字体，印刷级排版
- **响应式设计** — 完整移动端支持，侧边栏滑出
- **文件存储** — 笔记以 `.md` + `.meta.json` 分离存储，方便备份迁移

## 快速开始

```bash
# 克隆
git clone https://github.com/syskuku/misho-notes.git
cd misho-notes

# 安装依赖
pip install -r requirements.txt

# 启动
python app.py
```

打开 `http://localhost:1145`，默认密码 `changeme`。

## 配置

通过环境变量配置：

```bash
MISHO_PASSWORD=你的密码       # 登录密码（默认：changeme）
MISHO_PORT=8080               # 端口（默认：1145）
MISHO_DATA_DIR=/path/to/data  # 数据目录（默认：./data）
```

## 项目结构

```
misho-notes/
├── app.py              # Flask 后端
├── requirements.txt
├── .gitignore
├── static/
│   └── index.html      # 单文件前端（HTML + CSS + JS）
└── data/               # 运行时自动创建
    ├── sections.json
    ├── shares.json
    └── {分区ID}/
        ├── {笔记ID}.md
        └── {笔记ID}.meta.json
```

## 技术栈

- **后端** — Flask、Python-Markdown
- **前端** — 原生 JS（无框架）、Marked.js、Highlight.js、KaTeX
- **字体** — Noto Serif SC、Noto Sans SC
- **设计** — 侘寂美学：暖纸色、墨线点缀、衬线排版

## 部署

### Gunicorn

```bash
pip install gunicorn
MISHO_PASSWORD=你的密码 gunicorn -w 4 -b 0.0.0.0:1145 app:app
```

### Nginx 反向代理

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

## 许可证

MIT
