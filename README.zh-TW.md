# ✿ Misho Notes

[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md)

輕量級自託管 Markdown 筆記本，日式侘寂美學風格。

未書 — 未書寫之美的所在。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.0+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 特性

- **Markdown 編輯器** — 即時預覽，語法高亮（Highlight.js）
- **數學公式** — KaTeX 渲染 LaTeX（`$行內$` / `$$獨立區塊$$`）
- **分區與標籤** — 自訂圖示、顏色分區，標籤分類管理
- **分享連結** — 產生公開連結，單頁 HTML 展示，無需登入
- **列印排版** — Noto Serif SC 襯線字體，印刷級排版
- **響應式設計** — 完整行動裝置支援，側邊欄滑出
- **檔案儲存** — 筆記以 `.md` + `.meta.json` 分離儲存，方便備份遷移

## 快速開始

```bash
# 複製
git clone https://github.com/syskuku/misho-notes.git
cd misho-notes

# 安裝依賴
pip install -r requirements.txt

# 啟動
python app.py
```

開啟 `http://localhost:1145`，預設密碼 `changeme`。

## 設定

透過環境變數設定：

```bash
MISHO_PASSWORD=你的密碼       # 登入密碼（預設：changeme）
MISHO_PORT=8080               # 連接埠（預設：1145）
MISHO_DATA_DIR=/path/to/data  # 資料目錄（預設：./data）
```

## 專案結構

```
misho-notes/
├── app.py              # Flask 後端
├── requirements.txt
├── .gitignore
├── static/
│   └── index.html      # 單檔前端（HTML + CSS + JS）
└── data/               # 執行時自動建立
    ├── sections.json
    ├── shares.json
    └── {分區ID}/
        ├── {筆記ID}.md
        └── {筆記ID}.meta.json
```

## 技術堆疊

- **後端** — Flask、Python-Markdown
- **前端** — 原生 JS（無框架）、Marked.js、Highlight.js、KaTeX
- **字型** — Noto Serif SC、Noto Sans SC
- **設計** — 侘寂美學：暖紙色、墨線點綴、襯線排版

## 部署

### Gunicorn

```bash
pip install gunicorn
MISHO_PASSWORD=你的密碼 gunicorn -w 4 -b 0.0.0.0:1145 app:app
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

## 授權條款

MIT
