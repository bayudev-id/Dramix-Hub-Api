from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse, Response
import dataclasses
import requests
from moviebox import MovieBox
from models.home import SubjectMovie
import io

# Import Pillow for image resizing
try:
    from PIL import Image
except ImportError:
    Image = None

app = FastAPI(title="MovieBox Local API Wrapper")

import os

# Inisialisasi API wrapper
# Ganti token dengan milik Anda jika perlu akses khusus
token = os.environ.get("MOVIEBOX_TOKEN") or None
api = MovieBox(token=token, lang="id")

INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieBox API</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0b0f1a;
            --card-bg: rgba(23, 28, 41, 0.8);
            --primary: #38bdf8;
            --secondary: #818cf8;
            --text: #f1f5f9;
            --text-dim: #94a3b8;
            --accent: #10b981;
            --border: rgba(255, 255, 255, 0.08);
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg);
            background-image: radial-gradient(circle at 0% 0%, #1e1b4b 0%, transparent 40%),
                              radial-gradient(circle at 100% 100%, #0c4a6e 0%, transparent 40%);
            background-attachment: fixed;
            color: var(--text);
            margin: 0;
            padding: 0;
            min-height: 100vh;
        }
        .container {
            max-width: 1000px;
            margin: 40px auto;
            padding: 0 20px;
        }
        header {
            text-align: center;
            margin-bottom: 50px;
        }
        h1 {
            font-size: 2.8rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #fff 0%, var(--primary) 50%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            letter-spacing: -1px;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent);
            padding: 6px 16px;
            border-radius: 100px;
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid rgba(16, 185, 129, 0.2);
            backdrop-filter: blur(5px);
        }
        .dot {
            height: 8px;
            width: 8px;
            background-color: var(--accent);
            border-radius: 50%;
            margin-right: 10px;
            box-shadow: 0 0 12px var(--accent);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
            100% { opacity: 1; transform: scale(1); }
        }

        /* Endpoints List */
        .endpoints-stack {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .endpoint-card {
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 16px;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .endpoint-card.active {
            border-color: rgba(56, 189, 248, 0.4);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }

        .endpoint-header {
            padding: 18px 24px;
            display: flex;
            align-items: center;
            cursor: pointer;
            user-select: none;
            gap: 15px;
        }
        .endpoint-header:hover {
            background: rgba(255, 255, 255, 0.02);
        }
        .method-tag {
            font-size: 0.7rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 6px;
            min-width: 45px;
            text-align: center;
            background: var(--primary);
            color: #000;
        }
        .endpoint-url {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            font-weight: 500;
            flex: 1;
        }
        .endpoint-title {
            font-size: 0.85rem;
            color: var(--text-dim);
        }
        .chevron {
            transition: transform 0.3s;
            color: var(--text-dim);
        }
        .endpoint-card.active .chevron {
            transform: rotate(180deg);
            color: var(--primary);
        }

        .endpoint-body {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            border-top: 0 solid var(--border);
        }
        .endpoint-card.active .endpoint-body {
            max-height: 2000px;
            border-top-width: 1px;
        }

        .tester-content {
            padding: 24px;
        }

        /* Parameter Grid */
        .params-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .input-box {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .input-box label {
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-dim);
            padding-left: 4px;
        }
        .input-box input, .input-box select {
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 14px;
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.2s;
            backdrop-filter: blur(10px);
        }
        .input-box select {
            cursor: pointer;
            appearance: none;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
            background-repeat: no-repeat;
            background-position: right 12px center;
            background-size: 16px;
            padding-right: 40px;
        }
        .input-box select option {
            background-color: #0b0f1a;
            color: #fff;
        }
        .input-box input:focus, .input-box select:focus {
            border-color: var(--primary);
            background: rgba(56, 189, 248, 0.05);
        }

        .btn-run {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: #fff;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.3);
        }
        .btn-run:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(56, 189, 248, 0.4);
        }
        .btn-run:active { transform: translateY(0); }

        /* Response View */
        .response-box {
            margin-top: 25px;
            border-radius: 12px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            display: none;
        }
        .response-header {
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8rem;
        }
        .meta-tags {
            display: flex;
            gap: 15px;
        }
        .tag { font-weight: 600; }
        .tag-success { color: var(--accent); }
        .tag-time { color: var(--secondary); }

        .response-body {
            padding: 20px;
            max-height: 600px;
            overflow: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #a5d6ff;
            line-height: 1.5;
        }

        /* JSON Rendering Styles */
        .json-row { position: relative; padding-left: 18px; white-space: normal; word-wrap: break-word; }
        .json-toggle {
            position: absolute; left: 0; cursor: pointer; color: var(--text-dim);
            user-select: none; width: 15px; text-align: center; font-weight: bold;
        }
        .json-toggle:hover { color: var(--primary); }
        .json-collapsed > .json-content { display: none; }
        .json-collapsed > .json-placeholder { display: inline; color: var(--text-dim); }
        .json-placeholder { display: none; }
        .json-indent { border-left: 1px solid rgba(255,255,255,0.1); margin-left: 6px; }
        .json-key { color: var(--secondary); font-weight: 600; }
        .json-string { color: var(--accent); white-space: pre-wrap; word-break: break-all; display: inline; }
        .json-number { color: var(--primary); }
        .json-boolean { color: #f59e0b; }
        .json-null { color: #94a3b8; font-style: italic; }

        .url-display {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--primary);
            word-break: break-all;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .url-display span { flex: 1; opacity: 0.8; }
        .btn-copy-url {
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.2);
            color: var(--primary);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.7rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-copy-url:hover { background: var(--primary); color: #000; }

        .info-text {
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: -12px;
            margin-bottom: 18px;
            padding: 8px 12px;
            background: rgba(129, 140, 248, 0.05);
            border-radius: 8px;
            border-left: 3px solid var(--secondary);
        }
        .info-text b { color: var(--secondary); }

        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

        .footer {
            text-align: center;
            margin-top: 60px;
            padding-bottom: 40px;
            color: var(--text-dim);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="status-badge">
                <span class="dot"></span>
                <span id="server-status">Server Online</span>
                <span style="margin: 0 10px; opacity: 0.3">|</span>
                <span style="font-size: 0.75rem; color: var(--text-dim)">IP: </span>
                <code id="server-ip" style="color: var(--secondary); font-family: 'JetBrains Mono'; font-size: 0.8rem">...</code>
                <span style="margin: 0 10px; opacity: 0.3">|</span>
                <span style="font-size: 0.75rem; color: var(--text-dim)">ISP: </span>
                <span id="server-isp" style="color: var(--accent); font-size: 0.8rem; font-weight: 600">...</span>
                <span style="margin: 0 10px; opacity: 0.3">|</span>
                <span style="font-size: 0.75rem; color: var(--text-dim)">Region: </span>
                <span id="server-region" style="color: #f59e0b; font-size: 0.8rem; font-weight: 600">...</span>
            </div>
            <h1>MovieBox API</h1>
            <p style="color: var(--text-dim)">Professional Proxy Interface for Stream & Content Management</p>
        </header>

        <div class="endpoints-stack">

            <!-- CATEGORIES -->
            <div class="endpoint-card" id="card-cats">
                <div class="endpoint-header" onclick="toggleCard('card-cats')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/categories</span>
                    <span class="endpoint-title">Genres & Sections</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-cats-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-cats">/categories?lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-cats')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('cats', '/categories')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-cats">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-cats">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-cats">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-cats')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-cats" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- REKOMENDASI / CONTENT -->
            <div class="endpoint-card" id="card-content">
                <div class="endpoint-header" onclick="toggleCard('card-content')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/content</span>
                    <span class="endpoint-title">Recommendation Hijack</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>opId</label>
                                <input type="text" id="p-content-opId" value="3521493905000087296">
                            </div>
                            <div class="input-box">
                                <label>Page</label>
                                <input type="number" id="p-content-page" value="0">
                            </div>
                            <div class="input-box">
                                <label>Per Page</label>
                                <input type="number" id="p-content-perPage" value="18">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-content-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="info-text">
                            💡 Hanya opId <b>3521493905000087296</b> (Rekomendasi) yang mendukung parameter <b>Page</b> & <b>Per Page</b>.
                        </div>
                        <div class="url-display">
                            <span id="full-url-content">/content?opId=3521493905000087296&page=0&perPage=18&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-content')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('content', '/content')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-content">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-content">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-content">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-content')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-content" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- DETAIL -->
            <div class="endpoint-card" id="card-detail">
                <div class="endpoint-header" onclick="toggleCard('card-detail')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/detail</span>
                    <span class="endpoint-title">Movie Information</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Detail Path (Slug)</label>
                                <input type="text" id="p-detail-detailPath" value="">
                            </div>
                            <div class="input-box">
                                <label>Subject ID (Optional)</label>
                                <input type="text" id="p-detail-subjectId" value="6524447992693806504">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-detail-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-detail">/detail?detailPath=&subjectId=6524447992693806504&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-detail')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('detail', '/detail')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-detail">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-detail">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-detail">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-detail')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-detail" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PLAY -->
            <div class="endpoint-card" id="card-play">
                <div class="endpoint-header" onclick="toggleCard('card-play')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/play</span>
                    <span class="endpoint-title">Stream & Subtitles</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Subject ID</label>
                                <input type="text" id="p-play-subjectId" value="6524447992693806504">
                            </div>
                            <div class="input-box">
                                <label>Season (S:E)</label>
                                <input type="text" id="p-play-season" value="0:1" placeholder="0:1, 1:1, 1:5">
                            </div>
                            <div class="input-box">
                                <label>Episode</label>
                                <input type="text" id="p-play-episode" value="" placeholder="fallback jika season tanpa :">
                            </div>
                            <div class="input-box">
                                <label>Detail Path</label>
                                <input type="text" id="p-play-detailPath" value="" placeholder="movie-slug-abc123">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-play-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-play">/play?subjectId=6524447992693806504&season=0:1&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-play')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('play', '/play')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-play">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-play">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-play">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-play')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-play" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TRENDING -->
            <div class="endpoint-card" id="card-trending">
                <div class="endpoint-header" onclick="toggleCard('card-trending')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/trending</span>
                    <span class="endpoint-title">Trending Feed</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Page</label>
                                <input type="number" id="p-trending-page" value="0">
                            </div>
                            <div class="input-box">
                                <label>Per Page</label>
                                <input type="number" id="p-trending-perPage" value="18">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-trending-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-trending">/trending?page=0&perPage=18&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-trending')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('trending', '/trending')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-trending">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-trending">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-trending">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-trending')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-trending" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- DETAIL LENGKAP -->
            <div class="endpoint-card" id="card-detail-full">
                <div class="endpoint-header" onclick="toggleCard('card-detail-full')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/detail-content-lengkap</span>
                    <span class="endpoint-title">Full Content Details</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Detail Path / Slug</label>
                                <input type="text" id="p-detail-full-detailPath" value="money-heist-indonesian-IAxJOKGVGe5">
                            </div>
                            <div class="input-box">
                                <label>Subject ID (Optional)</label>
                                <input type="text" id="p-detail-full-subjectId" value="">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-detail-full-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردو (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-detail-full">/detail-content-lengkap?detailPath=money-heist-indonesian-IAxJOKGVGe5&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-detail-full')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('detail-full', '/detail-content-lengkap')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-detail-full">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-detail-full">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-detail-full">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-detail-full')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-detail-full" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SEARCH -->
            <div class="endpoint-card" id="card-search">
                <div class="endpoint-header" onclick="toggleCard('card-search')">
                    <span class="method-tag">GET</span>
                    <span class="endpoint-url">/search</span>
                    <span class="endpoint-title">Global Search</span>
                    <span class="chevron">▼</span>
                </div>
                <div class="endpoint-body">
                    <div class="tester-content">
                        <div class="params-grid">
                            <div class="input-box">
                                <label>Keyword</label>
                                <input type="text" id="p-search-keyword" value="Naruto">
                            </div>
                            <div class="input-box">
                                <label>Language</label>
                                <select id="p-search-lang">
                                    <option value="id">Bahasa Indonesia (id)</option>
                                    <option value="en">English (en)</option>
                                    <option value="ar">العربية (ar)</option>
                                    <option value="fr">Français (fr)</option>
                                    <option value="hi">हिन्दी (hi)</option>
                                    <option value="fil">Filipino (fil)</option>
                                    <option value="ur">اردo (ur)</option>
                                </select>
                            </div>
                        </div>
                        <div class="url-display">
                            <span id="full-url-search">/search?keyword=Naruto&lang=id</span>
                            <button class="btn-copy-url" onclick="copyUrl('full-url-search')">COPY URL</button>
                        </div>
                        <button class="btn-run" onclick="runSmartTest('search', '/search')">
                            <span>🚀</span> Run Request
                        </button>
                        <div class="response-box" id="res-search">
                            <div class="response-header">
                                <div class="meta-tags">
                                    <span class="tag">Status: <span class="tag-success" id="stat-search">-</span></span>
                                    <span class="tag">Time: <span class="tag-time" id="time-search">0 ms</span></span>
                                </div>
                                <button onclick="copyRes('body-search')" style="background:none; border:none; color:var(--primary); cursor:pointer; font-weight:600">Copy JSON</button>
                            </div>
                            <div id="body-search" class="response-body"></div>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <div class="footer">
            MovieBox API &bull; Premium Proxy Dashboard &bull; FastAPI v1.0
        </div>
    </div>

    <script>
        // Fetch Server Info (IP, ISP, Region)
        async function fetchServerInfo() {
            try {
                const res = await fetch('/server-info');
                const data = await res.json();
                document.getElementById('server-ip').innerText = data.ip || "Unknown";
                document.getElementById('server-isp').innerText = data.isp || "Unknown";
                document.getElementById('server-region').innerText = data.location || "Unknown";
                if (data.system) {
                    console.log("Server System:", data.system);
                }
            } catch (e) {
                document.getElementById('server-ip').innerText = "Unknown";
            }
        }
        fetchServerInfo();

        function toggleCard(id) {
            const card = document.getElementById(id);
            const wasActive = card.classList.contains('active');
            document.querySelectorAll('.endpoint-card').forEach(c => c.classList.remove('active'));
            if (!wasActive) {
                card.classList.add('active');
                // Auto update URL when card opens
                const prefix = id.replace('card-', '');
                const endpoint = card.querySelector('.endpoint-url').innerText;
                updateFullUrlDisplay(prefix, endpoint);
            }
        }

        // Listen for changes in inputs
        document.addEventListener('input', (e) => {
            const card = e.target.closest('.endpoint-card');
            if (card) {
                const id = card.id.replace('card-', '');
                const endpoint = card.querySelector('.endpoint-url').innerText;
                updateFullUrlDisplay(id, endpoint);
            }
        });

        function updateFullUrlDisplay(id, endpoint) {
            const card = document.getElementById(`card-${id}`);
            const inputs = card.querySelectorAll(`[id^="p-${id}-"]`);
            const params = new URLSearchParams();
            inputs.forEach(input => { if (input.value) params.append(input.id.replace(`p-${id}-`, ''), input.value); });
            const fullUrl = `${window.location.origin}${endpoint}?${params.toString()}`;
            document.getElementById(`full-url-${id}`).innerText = fullUrl;
        }

        async function runSmartTest(id, endpoint) {
            const statusLabel = document.getElementById(`stat-${id}`);
            const timeLabel = document.getElementById(`time-${id}`);
            const responseBox = document.getElementById(`res-${id}`);
            const responseBody = document.getElementById(`body-${id}`);
            responseBox.style.display = 'block';
            responseBody.innerHTML = '<div style="color:var(--text-dim); animation:pulse 1s infinite">Executing request...</div>';
            statusLabel.innerText = 'WAITING';
            statusLabel.style.color = 'var(--secondary)';
            const card = document.getElementById(`card-${id}`);
            const inputs = card.querySelectorAll(`[id^="p-${id}-"]`);
            const params = new URLSearchParams();
            inputs.forEach(input => { if (input.value) params.append(input.id.replace(`p-${id}-`, ''), input.value); });
            const startTime = performance.now();
            try {
                const response = await fetch(`${endpoint}?${params.toString()}`);
                const data = await response.json();
                statusLabel.innerText = `${response.status} ${response.statusText}`;
                statusLabel.style.color = response.ok ? 'var(--accent)' : '#ef4444';
                timeLabel.innerText = `${Math.round(performance.now() - startTime)} ms`;
                responseBody.innerHTML = '';
                responseBody.appendChild(createJsonNode(data));
            } catch (err) {
                statusLabel.innerText = 'ERROR';
                statusLabel.style.color = '#ef4444';
                responseBody.innerHTML = `<div style="color:#ef4444">Failed: ${err.message}</div>`;
            }
        }

        function createJsonNode(data, key = null) {
            const container = document.createElement('div');
            container.className = 'json-row';
            if (key !== null) {
                const keySpan = document.createElement('span');
                keySpan.className = 'json-key';
                keySpan.innerText = `"${key}": `;
                container.appendChild(keySpan);
            }
            if (data === null) {
                const span = document.createElement('span');
                span.className = 'json-null';
                span.innerText = 'null';
                container.appendChild(span);
            } else if (typeof data === 'object') {
                const isArray = Array.isArray(data);
                const toggle = document.createElement('span');
                toggle.className = 'json-toggle';
                toggle.innerText = '−';
                const openBrace = document.createTextNode(isArray ? '[' : '{');
                const content = document.createElement('div');
                content.className = 'json-indent json-content';
                const placeholder = document.createElement('span');
                placeholder.className = 'json-placeholder';
                placeholder.innerText = ' ... ';
                const keys = Object.keys(data);
                keys.forEach((k, index) => {
                    const row = createJsonNode(data[k], isArray ? null : k);
                    if (index < keys.length - 1) row.appendChild(document.createTextNode(','));
                    content.appendChild(row);
                });
                const closeBrace = document.createElement('div');
                closeBrace.innerText = isArray ? ']' : '}';
                toggle.onclick = (e) => {
                    e.stopPropagation();
                    container.classList.toggle('json-collapsed');
                    toggle.innerText = container.classList.contains('json-collapsed') ? '+' : '−';
                };
                container.appendChild(toggle);
                container.appendChild(openBrace);
                container.appendChild(placeholder);
                container.appendChild(content);
                container.appendChild(closeBrace);
            } else {
                const span = document.createElement('span');
                span.className = typeof data === 'string' ? 'json-string' : typeof data === 'number' ? 'json-number' : 'json-boolean';
                span.innerText = typeof data === 'string' ? `"${data}"` : data;
                container.appendChild(span);
            }
            return container;
        }

        function copyRes(id) {
            navigator.clipboard.writeText(document.getElementById(id).innerText);
            alert('JSON Copied!');
        }

        function copyUrl(id) {
            navigator.clipboard.writeText(document.getElementById(id).innerText);
            alert('URL Copied!');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def read_root():
    return INDEX_HTML

@app.get("/raw-home")
def get_home(lang: str = "id"):
    """Endpoint untuk mendapatkan data halaman Home."""
    api.set_lang(lang)
    home_data = api.home.get_home()
    return dataclasses.asdict(home_data)

@app.get("/categories")
def get_categories(lang: str = "id"):
    """Endpoint untuk mendapatkan daftar kategori (genreTopId) dari Home."""
    # Mapping judul sesuai bahasa
    titles = {
        "id": "Rekomendasi ✨",
        "en": "Recommended ✨",
        "ar": "توصيات ✨",
        "fr": "Recommandations ✨",
        "hi": "सिफारिशें ✨",
        "fil": "Mga Rekomendasyon ✨",
        "ur": "سفارشات ✨"
    }
    title = titles.get(lang, titles["id"])

    api.set_lang(lang)
    home_data = api.home.get_home()
    categories = []
    
    # Tambahkan data trending di PALING ATAS sesuai permintaan user
    categories.append({
        "title": title,
        "type": "SUBJECTS_MOVIE",
        "opId": "3521493905000087296"
    })
    
    for section in home_data.sections:
        genre_id = section.raw_data.get("genreTopId")
        op_id = section.raw_data.get("opId")
        
        # Sembunyikan tipe CUSTOM, FILTER, dan SPORT_LIVE sesuai permintaan user
        if section.type in ["CUSTOM", "FILTER", "SPORT_LIVE"]:
            continue
            
        # Ambil jika memiliki opId
        if op_id and str(op_id).strip():
            # Jangan masukkan lagi jika ini adalah opId yang sudah kita hijack (untuk keamanan)
            if str(op_id) != "3521493905000087296":
                categories.append({
                    "title": section.title,
                    "type": section.type,
                    "opId": str(op_id)
                })
            
    return {
        "code": 200,
        "message": "success",
        "provider": "moviebox",
        "data": categories
    }


@app.get("/debug")
def debug_info():
    import os
    env_token = os.environ.get("MOVIEBOX_TOKEN")
    token_len = len(env_token) if env_token else 0
    token_prefix = env_token[:25] if env_token else "None"
    
    # Test search
    try:
        test_results = api.search.search(keyword="The First Frost")
        search_status = f"Success ({test_results.debug_raw_count} results)"
    except Exception as e:
        search_status = f"Failed: {e}"

    return {
        "moviebox_token_env_length": token_len,
        "moviebox_token_env_prefix": token_prefix,
        "search_status": search_status,
        "client_token": api.client.token[:25] if api.client.token else "None",
        "default_token_used": api.client.token is None
    }

@app.get("/trending")
def get_trending(page: int = 0, perPage: int = 18, lang: str = "id"):
    """Endpoint untuk mendapatkan data Saran / Trending."""
    # Mapping judul sesuai bahasa
    titles = {
        "id": "Rekomendasi ✨",
        "en": "Recommended ✨",
        "ar": "توصيات ✨",
        "fr": "Recommandations ✨",
        "hi": "सिफारिशें ✨",
        "fil": "Mga Rekomendasyon ✨",
        "ur": "سفارشات ✨"
    }
    title = titles.get(lang, titles["id"])
    
    try:
        api.set_lang(lang)
        trending_data = api.home.get_trending(page=page, per_page=perPage)
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "title": title,
            "data": [dataclasses.asdict(s) for s in trending_data.subjects],
            "pager": dataclasses.asdict(trending_data.pager) if trending_data.pager else None
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil data trending: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/content")
def get_content(opId: str, page: int = 0, perPage: int = 18, lang: str = "id"):
    """Endpoint untuk mendapatkan daftar film dari section operasional (seperti Banner)."""
    # Mapping judul untuk trending hijack
    titles = {
        "id": "Rekomendasi ✨",
        "en": "Recommended ✨",
        "ar": "توصيات ✨",
        "fr": "Recommandations ✨",
        "hi": "सिफारिशें ✨",
        "fil": "Mga Rekomendasyon ✨",
        "ur": "سفارشات ✨"
    }
    title = titles.get(lang, titles["id"])

    try:
        api.set_lang(lang)
        
        # JIKA opId adalah ID khusus trending, alihkan ke logic trending
        if str(opId) == "3521493905000087296":
            trending_data = api.home.get_trending(page=page, per_page=perPage)
            return {
                "code": 200,
                "message": "success",
                "provider": "moviebox",
                "title": title,
                "data": [dataclasses.asdict(s) for s in trending_data.subjects],
                "pager": dataclasses.asdict(trending_data.pager) if trending_data.pager else None
            }

        result = api.home.get_operational_content(op_id=opId)
        
        if "error" in result:
            return JSONResponse(status_code=404, content={
                "code": 404,
                "message": result["error"],
                "provider": "moviebox",
                "data": None
            })
            
        # Kita normalisasi data subjects jika ada
        from models.home import SubjectMovie
        subjects_raw = result.get("data", [])
        subjects = [dataclasses.asdict(SubjectMovie.from_dict(s)) for s in subjects_raw]
        
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "title": result.get("title", ""),
            "type": result.get("type", ""),
            "data": subjects
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil data operasional: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/search")
def search_movies(keyword: str, page: int = 1, perPage: int = 10, subjectType: int = 0, lang: str = "id"):
    """Endpoint untuk mencari film berdasarkan kata kunci."""
    try:
        api.set_lang(lang)
        results = api.search.search(keyword=keyword, page=page, per_page=perPage, subject_type=subjectType)
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "data": [dataclasses.asdict(s) for s in results.data],
            "pager": dataclasses.asdict(results.pager) if results.pager else None,
            "debug_raw_count": results.debug_raw_count
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal melakukan pencarian: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/detail")
def get_movie_detail(detailPath: str = "", subjectId: str = "", lang: str = "id"):
    """Endpoint untuk mendapatkan detail film berdasarkan path/slug atau subjectId."""
    import re
    api.set_lang(lang)

    LANG_SUFFIXES = [
        "-indonesian-", "-english-", "-malay-", "-arabic-", "-hindi-",
        "-thai-", "-vietnamese-", "-french-", "-portuguese-", "-russian-"
    ]

    def try_detail(path, sid=""):
        try:
            detail = api.detail.get_detail(detail_path=path, subject_id=sid)
            d = dataclasses.asdict(detail)
            # Pastikan ada isi minimal
            if d.get("title") or d.get("subject_id"):
                return d
        except Exception:
            pass
        return None

    # 1. Coba detailPath asli
    result = try_detail(detailPath, subjectId) if detailPath else None

    # 2. Jika gagal dan detailPath punya suffix bahasa, cari via search
    if result is None and detailPath:
        stripped = detailPath
        has_lang_suffix = False
        for suffix in LANG_SUFFIXES:
            if suffix in detailPath:
                stripped = detailPath[:detailPath.index(suffix)]
                has_lang_suffix = True
                break

        if not has_lang_suffix:
            # Hapus hash ID di ujung: "movie-title-ABC123xyz" → "movie-title"
            stripped = re.sub(r'-[A-Za-z0-9]{8,}$', '', detailPath)

        keyword = stripped.replace('-', ' ').strip()
        if keyword:
            try:
                raw = api.client.get("/wefeed-h5api-bff/subject/search",
                                     params={"keyword": keyword, "page": 1, "perPage": 10})
                raw_items = raw.get("subjectList", raw.get("items", []))

                for item in raw_items:
                    candidate = item.get("detailPath", "") if isinstance(item, dict) else ""
                    corner = item.get("corner", "") if isinstance(item, dict) else ""
                    if not candidate or corner:  # skip jika tidak ada path atau versi dub
                        continue
                    result = try_detail(candidate)
                    if result:
                        break
            except Exception:
                pass

    # 3. Masih gagal + ada subjectId → fallback recommendations
    if result is None and subjectId:
        try:
            rec = api.detail.get_recommendations(subject_id=subjectId, page=1, per_page=5)
            for item in rec.get("items", []):
                candidate = item.get("detailPath", "")
                if candidate and not any(s in candidate for s in LANG_SUFFIXES):
                    result = try_detail(candidate)
                    if result:
                        break
        except Exception:
            pass

    if result:
        return {"code": 200, "message": "success", "provider": "moviebox", "data": result}

    return JSONResponse(status_code=502, content={
        "code": 502,
        "message": f"Gagal mengambil detail film: detailPath tidak valid atau film tidak tersedia.",
        "provider": "moviebox",
        "data": None
    })

@app.get("/recommendations")
def get_recommendations(subjectId: str, page: int = 1, perPage: int = 12, lang: str = "id"):
    """Endpoint untuk mendapatkan film-film rekomendasi/related berdasarkan subjectId.
    
    Endpoint ini langsung menggunakan /subject/detail-rec yang bekerja dengan subjectId.
    
    Contoh:
    - /recommendations?subjectId=8632466831183433976
    - /recommendations?subjectId=8632466831183433976&page=1&perPage=20
    """
    try:
        api.set_lang(lang)
        rec_data = api.detail.get_recommendations(subject_id=subjectId, page=page, per_page=perPage)
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "data": rec_data
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil rekomendasi: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/detail-content-lengkap")
def get_movie_detail_lengkap(detailPath: str = "", subjectId: str = "", lang: str = "id"):
    """Endpoint untuk mendapatkan detail film LENGKAP (100% RAW sesuai aslinya)."""
    try:
        api.set_lang(lang)
        raw_data = api.detail.get_detail_raw(detail_path=detailPath, subject_id=subjectId)
        return raw_data
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil detail film lengkap (RAW): {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/play")
def get_play_info(request: Request, subjectId: str, season: str = "", episode: int = 0, detailPath: str = ""):
    """Endpoint terpadu untuk mendapatkan link streaming dan daftar subtitle.

    Param season mendukung format:
      - "1:1" = Season 1, Episode 1 (serial)
      - "0:1" = Film (tanpa season), Episode 1
      - "1"   = Season 1, Episode 1 (default ep 1)
      - kosong = se=1, ep=1 (default)
    """
    try:
        base_url = str(request.base_url).rstrip("/")

        # Parse season format "S:E"
        se, ep = 1, 1
        if season:
            parts = season.split(":")
            se = int(parts[0]) if parts[0].strip() else 1
            ep = int(parts[1]) if len(parts) > 1 and parts[1].strip() else (episode or 1)
        elif episode:
            ep = episode

        # Jika detailPath belum ada, coba ambil dari detail via subjectId → recommendations
        if not detailPath:
            try:
                rec = api.detail.get_recommendations(subject_id=subjectId, page=1, per_page=5)
                for item in rec.get("items", []):
                    dp = item.get("detailPath", "")
                    if dp and not any(s in dp for s in ["-indonesian-", "-english-", "-malay-"]):
                        detailPath = dp
                        break
            except Exception as e:
                print(f"Warning: Gagal ambil detailPath dari recommendations: {e}")

        # 2. Ambil info streaming
        play_data = api.play.get_play_info(subject_id=subjectId, season=se, episode=ep, detail_path=detailPath)

        # 2b. Fallback: movie (se=0) + ep!=0 kosong → coba ep=0 (format movie asli)
        if not play_data.has_resource and se == 0 and ep != 0:
            play_data = api.play.get_play_info(subject_id=subjectId, season=se, episode=0, detail_path=detailPath)

        # 3. Jika ada stream, ambil subtitle menggunakan ID stream pertama
        if play_data.streams:
            first_stream = play_data.streams[0]
            try:
                captions = api.play.get_captions(
                    subject_id=subjectId, 
                    stream_id=first_stream.id, 
                    format=first_stream.format, 
                    detail_path=detailPath
                )
                play_data.captions = captions
            except Exception as cap_err:
                print(f"Warning: Gagal mengambil subtitle: {cap_err}")
                play_data.captions = []
        
        # 3. (REMOVED PROXY REWRITE)
                
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "data": dataclasses.asdict(play_data)
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil data playback terpadu: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/proxy/video")
def proxy_video(url: str, request: Request):
    """Proxy untuk memintas pengecekan Referer pada file video."""
    try:
        headers = {
            "Referer": "https://netfilm.world/spa/videoPlayPage/movies/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        #         
        # Support for Range requests (important for seeking)
        range_header = request.headers.get("range")
        if range_header:
            headers["Range"] = range_header

        # Stream the response
        res = requests.get(url, headers=headers, stream=True, timeout=30)
        
        # Exclude internal headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers_to_pass = {k: v for k, v in res.headers.items() if k.lower() not in excluded_headers}
        
        def iterfile():
            for chunk in res.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        return StreamingResponse(
            iterfile(),
            status_code=res.status_code,
            headers=headers_to_pass,
            media_type=res.headers.get("Content-Type", "video/mp4")
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/captions")
def get_captions(subjectId: str, streamId: str, format: str = "MP4", detailPath: str = ""):
    """Endpoint untuk mendapatkan daftar subtitle."""
    try:
        captions = api.detail.get_captions(subject_id=subjectId, stream_id=streamId, format=format, detail_path=detailPath)
        return {
            "code": 200,
            "message": "success",
            "provider": "moviebox",
            "data": [dataclasses.asdict(c) for c in captions]
        }
    except Exception as e:
        return JSONResponse(status_code=502, content={
            "code": 502,
            "message": f"Gagal mengambil subtitle: {str(e)}",
            "provider": "moviebox",
            "data": None
        })

@app.get("/api/resize-image")
def resize_image(url: str = Query(...), w: int = Query(150, ge=50, le=800)):
    """
    Image proxy: download, resize to thumbnail (max width {w}px), convert to WebP.
    Returns <15KB per image for typical covers.
    """
    if Image is None:
        # Fallback: proxy without resize if Pillow not installed
        try:
            resp = requests.get(url, timeout=10, stream=True)
            resp.raise_for_status()
            return StreamingResponse(
                resp.iter_content(chunk_size=8192),
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400, immutable",
                    "X-Proxy": "Dramix-Image-Proxy (passthrough)"
                }
            )
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})

    try:
        # Download with streaming
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()
        
        # Read image data
        img_data = io.BytesIO()
        for chunk in resp.iter_content(chunk_size=32768):
            if chunk:
                img_data.write(chunk)
        img_data.seek(0)
        
        # Open and convert to RGB (handle RGBA/P modes)
        img = Image.open(img_data)
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (0, 0, 0))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        
        # Resize maintaining aspect ratio
        orig_w, orig_h = img.size
        if orig_w > w:
            ratio = w / orig_w
            new_h = int(orig_h * ratio)
            img = img.resize((w, new_h), Image.LANCZOS)
        
        # Save as WebP with quality 80
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=80, method=6)
        output.seek(0)
        img_size_kb = output.getbuffer().nbytes / 1024
        
        return Response(
            content=output.getvalue(),
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=86400, immutable",
                "X-Proxy": "Dramix-Image-Proxy",
                "X-Original-Size": str(resp.headers.get("Content-Length", "unknown")),
                "X-Resized-Size": f"{img_size_kb:.1f}KB"
            }
        )
    except Exception as e:
        # Fallback: pass through original
        try:
            resp = requests.get(url, timeout=10, stream=True)
            resp.raise_for_status()
            return StreamingResponse(
                resp.iter_content(chunk_size=8192),
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
            )
        except:
            return JSONResponse(status_code=502, content={"error": str(e)})


@app.get("/server-info")
def get_server_info():
    """Endpoint internal untuk mendapatkan info server proxy (IP & ISP)."""
    try:
        # Menggunakan ip-api.com untuk mendapatkan IP dan ISP
        response = requests.get("http://ip-api.com/json/", timeout=5)
        data = response.json()
        if data.get("status") == "success":
            return {
                "ip": data.get("query"),
                "isp": data.get("isp"),
                "location": f"{data.get('city')}, {data.get('country')}",
                "system": "FastAPI Proxy"
            }
        return {"ip": "Local/Private", "isp": "Unknown", "system": "FastAPI Proxy"}
    except:
        return {"ip": "Error", "isp": "Error", "system": "FastAPI Proxy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 6104))
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("app:app", host=host, port=port, reload=False)
