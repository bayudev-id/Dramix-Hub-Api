import time
import uuid
import httpx
import json
import os
import asyncio
import struct
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional, Any

# Load .env (opsional; env vars dari platform juga didukung)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# OpenAPI / Swagger Metadata
# ============================================================
app = FastAPI(
    title="CineFlow API Proxy",
    description="""
    **CineFlow API Proxy** — Proxy server untuk API CineFlow.
    
    ## Fitur
    * 🔄 **Auto Token Refresh** — Token Bearer di-refresh otomatis
    * 📡 **Proxy Endpoints** — Forward request ke server CineFlow asli
    * 🔑 **Token Management** — Set, refresh, dan monitor token
    * 📊 **Dashboard** — UI interaktif untuk testing API
    
    ## Endpoints
    * `/api/modelles/*` — Content & Streaming (models, categories, videos, detail, source, download)
    * `/api/app/*` — Account, Auth, Payment
    * `/api/token/*` — Token management
    """,
    version="2.3.0",
    contact={
        "name": "CineFlow Proxy",
        "url": "http://127.0.0.1:8000",
    },
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================
# CORS - izinkan frontend lokal (vite dev & produksi)
# ============================================================
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])


# ============================================================
# Pydantic Models untuk Dokumentasi
# ============================================================
class TokenStatusResponse(BaseModel):
    has_token: bool
    has_refresh_token: bool
    token_preview: Optional[str] = None
    expires_in_seconds: float
    is_expired: bool
    refresh_token_preview: Optional[str] = None

class TokenSetRequest(BaseModel):
    refresh_token: str

class TokenSetResponse(BaseModel):
    code: int
    message: str
    token_preview: Optional[str] = None
    expires_in_seconds: Optional[int] = None

class TokenRefreshResponse(BaseModel):
    code: int
    message: str
    token_preview: Optional[str] = None

class ErrorResponse(BaseModel):
    code: int
    message: str

class ProxyResponse(BaseModel):
    code: int
    message: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Any] = None

class PairInitRequest(BaseModel):
    device_type: str = "android_tv"
    ui_mode: str = "tv"

class PairInitResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None

class PairPollResponse(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None

# ============================================================
# Dashboard HTML (Premium Design)
# ============================================================
def get_dashboard_html(token_preview, expires_in, is_expired, error_msg=None, profile=None):
    # Warna matang & professional: emerald accent, deep slate base (antislop R-01, R-29)
    status_color = "#10b981" if not is_expired else "#ef4444"
    status_text = "Active" if not is_expired else "Expired"
    
    # Extract profile data
    if profile is None:
        profile = {}
    email = profile.get("email", "unknown@example.com")
    user_id = profile.get("user_id", "N/A")
    device_type = profile.get("device_type", "N/A")
    display_name = profile.get("display_name", "User")
    
    # Generate avatar initials
    try:
        initials = "".join([word[0].upper() for word in display_name.split()[:2]])
        if not initials:
            initials = email[0].upper()
    except:
        initials = email[0].upper() if email else "U"
    
    # Error alert (simplified, no decorative styling)
    error_alert = ""
    if error_msg:
        error_alert = f"""
            <div style="background: rgba(239,68,68,0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 16px; margin-bottom: 20px; color: #fca5a5;">
                <div style="font-weight: 600; margin-bottom: 8px; font-size: 0.9rem;">Setup Required</div>
                <div style="font-size: 0.85rem; color: #fecaca; margin-bottom: 12px;">Error: {error_msg}</div>
                <div style="font-size: 0.8rem; color: #fca5a5;">Set a new refresh token below to continue.</div>
            </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CineFlow API Proxy Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <style>
            /* Antislop-compliant palette: deep slate + emerald accent (R-01, R-29) */
            :root {{
                --bg: #0f172a;
                --card-bg: #1e293b;
                --border: rgba(148, 163, 184, 0.2);
                --accent: #10b981;
                --text: #f1f5f9;
                --text-dim: #94a3b8;
                --code-bg: rgba(15, 23, 42, 0.6);
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                line-height: 1.6;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                padding: 32px 20px;
            }}
            header {{
                margin-bottom: 32px;
            }}
            h1 {{
                font-size: 1.75rem;
                margin: 0 0 12px 0;
                color: var(--text);
                font-weight: 600;
            }}
            .status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(16, 185, 129, 0.1);
                color: {status_color};
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: 500;
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            .dot {{
                height: 6px;
                width: 6px;
                background-color: {status_color};
                border-radius: 50%;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 380px 1fr;
                gap: 24px;
                align-items: start;
            }}
            .sidebar {{
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}
            .main-content {{
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}
            .card {{
                background: var(--card-bg);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 20px;
            }}
            .card:hover {{
                border-color: rgba(148, 163, 184, 0.3);
            }}
            .card h2 {{
                font-size: 1rem;
                margin: 0 0 16px 0;
                color: var(--text);
                font-weight: 600;
            }}
            /* Mobile responsive (R-03) */
            @media (max-width: 1024px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px 16px;
                }}
                h1 {{
                    font-size: 1.5rem;
                }}
                .card {{
                    padding: 16px;
                }}
            }}
            .token-val {{
                font-family: 'JetBrains Mono', monospace;
                background: var(--code-bg);
                padding: 12px;
                border-radius: 6px;
                word-break: break-all;
                font-size: 0.8rem;
                color: var(--accent);
                margin: 12px 0;
                border: 1px solid var(--border);
            }}
            .timer {{
                font-size: 1.5rem;
                font-weight: 600;
                margin: 12px 0;
                color: var(--text);
            }}
            .endpoint-list {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}
            .endpoint-item {{
                background: rgba(16, 185, 129, 0.05);
                margin-bottom: 8px;
                padding: 10px;
                border-radius: 6px;
                border-left: 3px solid var(--accent);
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
            }}
            .endpoint-item:hover {{
                background: rgba(16, 185, 129, 0.08);
            }}
            .method {{
                font-weight: 600;
                font-size: 0.65rem;
                padding: 3px 6px;
                border-radius: 3px;
                background: var(--accent);
                color: var(--bg);
                min-width: 32px;
                text-align: center;
            }}
            .url {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.75rem;
                color: var(--text-dim);
                overflow: hidden;
                text-overflow: ellipsis;
                flex: 1;
            }}
            .input-group {{
                display: flex;
                gap: 12px;
                margin-bottom: 16px;
            }}
            .method-select, input, textarea {{
                background: var(--code-bg);
                border: 1px solid var(--border);
                border-radius: 6px;
                color: var(--text);
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                outline: none;
                transition: border-color 0.2s;
            }}
            .method-select {{
                padding: 8px 12px;
                cursor: pointer;
                flex-shrink: 0;
            }}
            input {{
                flex: 1;
                padding: 10px 12px;
            }}
            textarea {{
                width: 100%;
                padding: 10px 12px;
                resize: vertical;
                font-size: 0.8rem;
            }}
            input:focus, textarea:focus, .method-select:focus {{
                border-color: var(--accent);
            }}
            .response-container {{
                background: var(--code-bg);
                border-radius: 6px;
                border: 1px solid var(--border);
                overflow: hidden;
            }}
            .response-header {{
                padding: 12px 16px;
                background: rgba(16, 185, 129, 0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.75rem;
                border-bottom: 1px solid var(--border);
            }}
            .response-body {{
                padding: 16px;
                max-height: 400px;
                overflow-y: auto;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
                white-space: pre-wrap;
                word-break: break-word;
                color: #a5d6ff;
                margin: 0;
            }}
            .meta-info {{
                display: flex;
                gap: 20px;
                color: var(--text-dim);
                font-size: 0.75rem;
            }}
            .status-ok {{ color: var(--accent); font-weight: 500; }}
            .status-err {{ color: #ef4444; font-weight: 500; }}
            .speed-tag {{ color: var(--accent); font-weight: 500; }}
            .copy-btn {{
                background: rgba(16, 185, 129, 0.15);
                border: 1px solid rgba(16, 185, 129, 0.3);
                color: var(--accent);
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 0.75rem;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
                font-weight: 500;
            }}
            .copy-btn:hover {{
                background: rgba(16, 185, 129, 0.25);
            }}
            .footer {{
                margin-top: 40px;
                padding: 24px 0;
                color: var(--text-dim);
                font-size: 0.75rem;
                text-align: center;
                border-top: 1px solid var(--border);
            }}
            .btn {{
                background: var(--accent);
                color: var(--bg);
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 0.85rem;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .btn:hover {{
                opacity: 0.9;
            }}
            .btn:active {{
                transform: scale(0.98);
            }}
            .btn:disabled {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            ::-webkit-scrollbar {{
                width: 6px;
                height: 6px;
            }}
            ::-webkit-scrollbar-track {{
                background: transparent;
            }}
            ::-webkit-scrollbar-thumb {{
                background: rgba(148, 163, 184, 0.2);
                border-radius: 3px;
            }}
            ::-webkit-scrollbar-thumb:hover {{
                background: rgba(148, 163, 184, 0.3);
            }}
        </style>
        <script>
            function refreshPage() {{ window.location.reload(); }}
            
            setInterval(() => {{
                const timerEl = document.getElementById('timer');
                if (timerEl) {{
                    let val = parseInt(timerEl.innerText);
                    if (!isNaN(val) && val > 0) {{
                        timerEl.innerText = val - 1;
                    }} else if (val === 0) {{
                        refreshPage();
                    }}
                }}
            }}, 1000);

            function toggleBodyInput() {{
                const method = document.getElementById('test-method').value;
                document.getElementById('body-input-container').style.display = method === 'POST' ? 'block' : 'none';
            }}

            function setTestUrl(url, method = 'GET', body = '') {{
                document.getElementById('test-url').value = url;
                document.getElementById('test-method').value = method;
                document.getElementById('test-body').value = body;
                toggleBodyInput();
            }}

            async function runTest() {{
                const urlInput = document.getElementById('test-url');
                const methodInput = document.getElementById('test-method');
                const bodyInput = document.getElementById('test-body');
                const runBtn = document.getElementById('run-btn');
                const responseBody = document.getElementById('response-body');
                const statusLabel = document.getElementById('status-label');
                const timeLabel = document.getElementById('time-label');
                
                const url = urlInput.value.trim();
                const method = methodInput.value;
                const bodyStr = bodyInput.value.trim();
                
                if (!url) return;

                runBtn.disabled = true;
                runBtn.innerText = 'Testing...';
                responseBody.innerText = '// Loading response data...';
                statusLabel.innerText = 'Waiting...';
                timeLabel.innerText = '0 ms';

                const fetchOptions = {{
                    method: method,
                    headers: {{}}
                }};

                if (method === 'POST' && bodyStr) {{
                    fetchOptions.headers['Content-Type'] = 'application/json';
                    fetchOptions.body = bodyStr;
                }}

                const startTime = performance.now();
                
                try {{
                    const response = await fetch(url, fetchOptions);
                    const endTime = performance.now();
                    const duration = Math.round(endTime - startTime);
                    
                    statusLabel.innerText = `HTTP ${{response.status}}`;
                    statusLabel.className = response.ok ? 'status-ok' : 'status-err';
                    timeLabel.innerText = `${{duration}} ms`;
                    
                    const data = await response.json();
                    responseBody.innerText = JSON.stringify(data, null, 2);
                }} catch (error) {{
                    statusLabel.innerText = 'Error';
                    statusLabel.className = 'status-err';
                    responseBody.innerText = `// Connection Error:\\n${{error.message}}`;
                }} finally {{
                    runBtn.disabled = false;
                    runBtn.innerText = 'Run Test';
                }}
            }}

            function copyResponse() {{
                const text = document.getElementById('response-body').innerText;
                
                // Coba clipboard API (HTTPS/localhost)
                if (navigator.clipboard) {{
                    navigator.clipboard.writeText(text).then(() => {{
                        const btn = document.getElementById('copy-btn');
                        const originalText = btn.innerHTML;
                        btn.innerHTML = '<span>✅</span> Copied!';
                        setTimeout(() => {{
                            btn.innerHTML = originalText;
                        }}, 2000);
                    }}).catch(() => fallbackCopy(text));
                }} else {{
                    // Fallback untuk HTTP: gunakan textarea + execCommand
                    fallbackCopy(text);
                }}
            }}

            function fallbackCopy(text) {{
                const textarea = document.createElement('textarea');
                textarea.value = text;
                textarea.style.position = 'fixed';
                textarea.style.opacity = '0';
                document.body.appendChild(textarea);
                textarea.select();
                try {{
                    document.execCommand('copy');
                    const btn = document.getElementById('copy-btn');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '<span>✅</span> Copied!';
                    setTimeout(() => {{
                        btn.innerHTML = originalText;
                    }}, 2000);
                }} catch (e) {{
                    alert('Copy gagal. Select manual.');
                }} finally {{
                    document.body.removeChild(textarea);
                }}
            }}

            function setRefreshToken() {{
                const refreshToken = document.getElementById('new-refresh-token').value;
                if (!refreshToken || !refreshToken.startsWith('cf_rt_')) {{
                    alert('ERROR: Token harus dimulai dengan cf_rt_');
                    return;
                }}
                
                fetch('/api/token/set', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{ refresh_token: refreshToken }})
                }})
                .then(r => r.json())
                .then(data => {{
                    if (data.code === 200) {{
                        alert('SUCCESS: Token telah diset! Server akan auto-refresh sekarang.');
                        document.getElementById('new-refresh-token').value = '';
                        setTimeout(() => location.reload(), 1000);
                    }} else {{
                        alert('ERROR: ' + (data.message || 'Gagal set token'));
                    }}
                }})
                .catch(e => alert('ERROR: ' + e.message));
            }}

            async function startPairing() {{
                try {{
                    const resp = await fetch('/api/auth/pair/init', {{method: 'POST'}});
                    const data = await resp.json();
                    if (data.code !== 200) {{
                        alert('ERROR: ' + (data.message || 'Gagal start pairing'));
                        return;
                    }}
                    
                    const pairingData = data.data;
                    const deviceCode = pairingData.device_code;
                    const userCode = pairingData.user_code;
                    const verificationUrl = pairingData.verification_uri_complete || pairingData.verification_uri;
                    const instanceId = pairingData._app_instance_id;
                    
                    document.getElementById('pair-status').style.display = 'block';
                    document.getElementById('pair-code-display').innerHTML = 
                        '<div style="background: rgba(16,185,137,0.1); border: 2px solid #10b981; border-radius: 12px; padding: 16px; margin-bottom: 12px;">' +
                            '<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 8px;">USER CODE:</div>' +
                            '<div style="font-family: monospace; font-size: 1.4rem; font-weight: 700; color: #10b981; letter-spacing: 2px; margin-bottom: 12px;">' + userCode + '</div>' +
                            '<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 8px;">ATAU buka link di browser:</div>' +
                            '<div><a href="' + verificationUrl + '" target="_blank" style="color: #38bdf8; word-break: break-all;">' + verificationUrl + '</a></div>' +
                        '</div>';
                    document.getElementById('pair-waiting').innerHTML = 'Menunggu approval...';
                    
                    pollPairingStatus(deviceCode, instanceId, pairingData.interval_seconds || 5);
                }} catch (e) {{
                    alert('ERROR: ' + e.message);
                }}
            }}

            async function pollPairingStatus(deviceCode, instanceId, interval) {{
                const maxAttempts = 180; // 15 menit dengan interval 5s
                let attempts = 0;
                
                const poll = async () => {{
                    attempts++;
                    if (attempts > maxAttempts) {{
                        document.getElementById('pair-waiting').innerHTML = '<div style="color: #ef4444;">⏰ Timeout! Pairing expired. Coba lagi.</div>';
                        return;
                    }}
                    
                    try {{
                        const resp = await fetch('/api/auth/pair/poll?device_code=' + encodeURIComponent(deviceCode) + '&app_instance_id=' + encodeURIComponent(instanceId));
                        const data = await resp.json();
                        
                        if (data.code === 200) {{
                            // Success!
                            document.getElementById('pair-code-display').innerHTML = 
                                '<div style="background: rgba(16,185,137,0.1); border: 2px solid #10b981; border-radius: 12px; padding: 16px;">' +
                                    '<div style="font-size: 1rem; font-weight: 700; color: #10b981; margin-bottom: 12px;">✅ Pairing Berhasil!</div>' +
                                    '<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 6px;">User: ' + (data.data.user_email || 'TV Device') + '</div>' +
                                    '<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 8px;">Token berlaku: ' + data.data.expires_in_seconds + 's</div>' +
                                '</div>';
                            document.getElementById('pair-waiting').innerHTML = '<div style="color: #10b981;">Proxy siap digunakan!</div>';
                            setTimeout(() => location.reload(), 2000);
                            return;
                        }} else if (data.code === 202) {{
                            // Still waiting
                            const elapsed = (attempts * interval).toFixed(0);
                            document.getElementById('pair-waiting').innerHTML = 'Menunggu approval... (' + elapsed + 's elapsed)';
                            setTimeout(poll, interval * 1000);
                        }} else {{
                            document.getElementById('pair-waiting').innerHTML = '<div style="color: #ef4444;">ERROR: ' + (data.message || 'Unknown error') + '</div>';
                        }}
                    }} catch (e) {{
                        document.getElementById('pair-waiting').innerHTML = '<div style="color: #ef4444;">Network error: ' + e.message + '</div>';
                    }}
                }};
                
                poll();
            }}
        </script>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>CineFlow Proxy</h1>
                <div class="status-badge">
                    <span class="dot"></span>{status_text}
                </div>
            </header>

            {error_alert}

            <div class="grid">
                <div class="sidebar">
                    <div class="card">
                        <h2>Available Endpoints</h2>
                        <p style="font-size: 0.75rem; color: var(--text-dim); margin: 0 0 12px 0;">Click to test</p>
                        <div class="endpoint-list">
                            <div style="font-size: 0.7rem; font-weight: 600; color: var(--accent); margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px;">Content & Streaming</div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/models')">
                                <span class="method">GET</span><span class="url">Models</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/categories?model_id=youku')">
                                <span class="method">GET</span><span class="url">Categories</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/videos?model_id=youku&category_id=home&page=1')">
                                <span class="method">GET</span><span class="url">Videos</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/detail?model_id=youku&id=')">
                                <span class="method">GET</span><span class="url">Detail</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/source?model_id=youku&episode_id=&id=')">
                                <span class="method">GET</span><span class="url">Source</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/download?model_id=youku&episode_id=&id=')">
                                <span class="method">GET</span><span class="url">Download</span>
                            </div>
                            <div class="endpoint-item" onclick="setTestUrl('/api/modelles/search', 'POST', '{{&quot;content_type&quot;:&quot;movie_tv&quot;,&quot;model_id&quot;:&quot;moviebox&quot;,&quot;page&quot;:1,&quot;q&quot;:&quot;money&quot;}}')">
                                <span class="method">POST</span><span class="url">Search</span>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h2>Account Profile</h2>
                        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                            <div style="width: 48px; height: 48px; border-radius: 50%; background: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 1.25rem; font-weight: 600; color: var(--bg); flex-shrink: 0;">
                                {initials}
                            </div>
                            <div style="flex: 1; min-width: 0;">
                                <div style="font-weight: 600; font-size: 0.9rem; color: var(--text); margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis;">
                                    {display_name}
                                </div>
                                <div style="font-size: 0.75rem; color: var(--text-dim); overflow: hidden; text-overflow: ellipsis;">
                                    {email}
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px;">
                            <span style="font-size: 0.7rem; padding: 4px 8px; border-radius: 4px; background: rgba(16, 185, 129, 0.1); color: var(--accent); font-weight: 500; border: 1px solid rgba(16, 185, 129, 0.2);">
                                {device_type}
                            </span>
                            <span style="font-size: 0.7rem; padding: 4px 8px; border-radius: 4px; background: rgba(16, 185, 129, 0.1); color: var(--accent); font-weight: 500; border: 1px solid rgba(16, 185, 129, 0.2);">
                                Logged In
                            </span>
                        </div>
                        <div style="padding-top: 12px; border-top: 1px solid var(--border);">
                            <div style="font-size: 0.7rem; color: var(--text-dim); margin-bottom: 4px;">User ID</div>
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--text-dim); background: var(--code-bg); padding: 6px 8px; border-radius: 4px; word-break: break-all; border: 1px solid var(--border);">
                                {user_id}
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h2>Token Session</h2>
                        <p style="font-size: 0.8rem; color: var(--text-dim); margin: 0 0 8px 0;">Current bearer token</p>
                        <div class="token-val">{token_preview}</div>
                        <p style="font-size: 0.8rem; color: var(--text-dim); margin: 12px 0 6px 0;">Auto refresh in</p>
                        <div class="timer"><span id="timer">{expires_in}</span><span style="font-size: 0.9rem; font-weight: 400; color: var(--text-dim);"> seconds</span></div>
                        <button class="btn" onclick="fetch('/api/token/refresh', {{method:'POST'}}).then(refreshPage)" style="width: 100%;">Refresh Now</button>
                    </div>

                    <div class="card">
                        <h2>Token Setup</h2>
                        <p style="font-size: 0.8rem; color: var(--text-dim); margin: 0 0 12px 0;">Set new refresh token if expired</p>
                        <input type="text" id="new-refresh-token" placeholder="cf_rt_..." style="width: 100%; margin-bottom: 12px;" />
                        <button class="btn" onclick="setRefreshToken()" style="width: 100%;">Set Token</button>
                    </div>

                    <div class="card">
                        <h2>TV Device Pairing</h2>
                        <p style="font-size: 0.8rem; color: var(--text-dim); margin: 0 0 12px 0;">Create independent TV session</p>
                        <button class="btn" onclick="startPairing()" style="width: 100%; background: rgba(16, 185, 129, 0.2); color: var(--accent); border: 1px solid var(--accent);">Pair TV Device</button>
                        <div id="pair-status" style="display: none; margin-top: 12px;">
                            <div id="pair-code-display"></div>
                            <div id="pair-waiting" style="font-size: 0.8rem; color: var(--text-dim); text-align: center; margin-top: 8px;"></div>
                        </div>
                    </div>
                </div>

                <div class="main-content">
                    <div class="card">
                        <h2>API Tester</h2>
                        <div class="input-group">
                            <select id="test-method" class="method-select" onchange="toggleBodyInput()">
                                <option value="GET">GET</option>
                                <option value="POST">POST</option>
                            </select>
                            <input type="text" id="test-url" placeholder="/api/modelles/..." value="/api/modelles/models">
                            <button class="btn" id="run-btn" onclick="runTest()">Run Test</button>
                        </div>
                        <div id="body-input-container" style="display: none; margin-bottom: 16px;">
                            <textarea id="test-body" placeholder="JSON Request Body..." rows="5"></textarea>
                        </div>

                        <div class="response-container">
                            <div class="response-header">
                                <div class="meta-info">
                                    <span>Status: <span id="status-label">-</span></span>
                                    <span>Time: <span id="time-label" class="speed-tag">0 ms</span></span>
                                </div>
                                <button class="copy-btn" id="copy-btn" onclick="copyResponse()">
                                    <span>📋</span>Copy JSON
                                </button>
                            </div>
                            <pre id="response-body" class="response-body">// Click 'Run Test' to see response data</pre>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                CineFlow Proxy Service v0.2.4 · Running on FastAPI
            </div>
        </div>
    </body>
    </html>
    """


# ============================================================
# Konfigurasi Target Server
# ============================================================
TARGET_BASE_URL = "https://ngintipya2.cineflow.my.id"
SESSION_URL = f"{TARGET_BASE_URL}/api/app/session"
NONCE_URL = f"{TARGET_BASE_URL}/api/app/auth/nonce"
REFRESH_TOKEN_URL = f"{TARGET_BASE_URL}/api/app/auth/refresh-token"

# TV Device Pairing (device-code flow)
PAIRING_URL = f"{TARGET_BASE_URL}/api/app/auth/device/pairing"
PAIRING_STATUS_URL = f"{TARGET_BASE_URL}/api/app/auth/device/status"
PAIRING_EXCHANGE_URL = f"{TARGET_BASE_URL}/api/app/auth/device/exchange"

# Header default yang dipakai oleh aplikasi CineFlow
DEFAULT_HEADERS = {
    "accept": "application/json",
    "user-agent": "CineFlow/0.2.7 (com.cineflow.app; Android 13; SDK 33)",
    "x-requested-with": "com.cineflow.app",
}

# Info device untuk request session (dari analisa/04 SESSION)
DEVICE_INFO = {
    "android_release": "13",
    "android_sdk_int": 33,
    "apk_sha256": "640bbc065c4849a3dc46bb8f5466ff1903acc60ca359763626b4270da7191d9c",
    "app_version_code": 7,
    "app_version_name": "0.2.7",
    "brand": "Xiaomi",
    "device_type": "android_mobile",
    "locale": "en-US",
    "manufacturer": "Xiaomi",
    "model": "Redmi 5 Plus",
    "package_name": "com.cineflow.app",
    "signer_sha256": "7a5435b95ad63fe27b2d3428b6dcef92b49f72bb269e42b1cede505c6ec74a1b",
    "ui_mode": "mobile",
}

# Identitas TV Device untuk pairing mandiri
TV_DEVICE_INFO = {
    "android_release": "13",
    "android_sdk_int": 33,
    "app_version_code": 12,
    "app_version_name": "0.2.8",
    "brand": "CineFlow Proxy",
    "device_type": "android_tv",
    "locale": "en-US",
    "manufacturer": "CineFlow",
    "model": "Proxy TV",
    "package_name": "com.cineflow.app",
    "ui_mode": "tv",
}

# Refresh token dari environment variable atau hardcoded untuk testing
# JANGAN commit token asli ke repo! Sebaiknya simpan di environment variable
INITIAL_REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN", "cf_rt_Dtiu8iWXtjt87exwAQpCDMuK1gRph5V1AxiPLOHHDdDFcA2NT2EBTg")

# ============================================================
# Supabase - storage utama untuk session/token (via env)
# ============================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_TABLE = "cineflow_sessions"

def _supabase_headers() -> dict:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }

# ============================================================
# Token Manager - Otomatis ambil & refresh Bearer Token (v2 Auth)
# ============================================================
class TokenManager:
    def __init__(self):
        import random
        self._init_id = random.randint(1000, 9999)  # Unique ID untuk debugging
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.expires_at: float = 0  # epoch timestamp kapan token expired
        self.app_instance_id: str | None = None  # di-load dari cache atau dari env/HP
        self._phone_profile: dict = {}  # profile data dari HP
        
        # app_instance_id dari HP atau env override
        phone_instance_id = os.environ.get("APP_INSTANCE_ID", "")
        
        # Gunakan /tmp untuk Vercel karena filesystem root bersifat Read-Only
        if os.environ.get("VERCEL"):
            self.cache_file = "/tmp/session_data.json"
        else:
            self.cache_file = "session_data.json"
            
        self._load_from_cache(phone_instance_id)

    def _load_from_cache(self, phone_instance_id: str):
        """Memuat token dari Supabase (utama) / cache disk (fallback)"""
        data = None
        from_supabase = False

        # 1) Prioritas: Supabase sebagai storage utama
        if self._supabase_enabled():
            data = self._read_from_supabase()
            if data:
                from_supabase = True
                print(f"[TOKEN:{self._init_id}] [OK] Token loaded dari Supabase, instance: {str(data.get('app_instance_id') or '')[:12]}...")

        # 2) Fallback: file cache lokal
        if not data:
            try:
                if os.path.exists(self.cache_file):
                    with open(self.cache_file, "r") as f:
                        data = json.load(f)
            except Exception as e:
                print(f"[TOKEN] [ERROR] Gagal load cache: {e}")
            if not data and not os.path.exists(self.cache_file):
                print("[TOKEN] [INFO] Cache tidak ditemukan, perlu setup token")

        if data:
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.expires_at = data.get("expires_at", 0)
            self.app_instance_id = data.get("app_instance_id")
            profile = data.get("phone_profile") or {}
            if profile:
                self._phone_profile = profile

            # Migrasi awal: data dari disk tapi belum ada di Supabase
            if not from_supabase and self._supabase_enabled():
                try:
                    self._write_to_supabase()
                    print("[TOKEN] [OK] Session di-upload ke Supabase (migrasi awal)")
                except Exception as e:
                    print(f"[TOKEN] [WARN] Gagal upload ke Supabase: {e}")

            # Cek apakah token masih valid
            if not self.is_expired() and self.app_instance_id and self.refresh_token:
                print(f"[TOKEN:{self._init_id}] [OK] Token loaded, instance: {self.app_instance_id[:12]}...")
                if profile.get("email"):
                    print(f"[TOKEN:{self._init_id}] [OK] User: {profile['email']}")
                return

            # Token expired tapi ada refresh token, siap untuk di-refresh
            if self.refresh_token and self.app_instance_id:
                print(f"[TOKEN:{self._init_id}] [INFO] Access token expired, akan auto-refresh saat dibutuhkan")
                if profile.get("email"):
                    print(f"[TOKEN:{self._init_id}] [INFO] User: {profile['email']}")
                return

            # Cache ada tapi tidak lengkap
            print("[TOKEN] [WARN] Cache tidak lengkap, perlu setup ulang")
        
        # Setup instance ID jika belum ada
        if not self.app_instance_id:
            if phone_instance_id:
                self.app_instance_id = phone_instance_id
                print(f"[TOKEN] [INFO] Pakai instance ID dari env: {self.app_instance_id[:12]}...")
            else:
                # Jangan langsung extract dari HP, biarkan user setup manual
                # Fallback: generate random (mungkin error mismatch, tapi coba dulu)
                self.app_instance_id = str(uuid.uuid4())
                print(f"[TOKEN] [INFO] Generate instance ID sementara: {self.app_instance_id[:12]}...")
                print(f"[TOKEN] [HINT] Set APP_INSTANCE_ID env untuk instance ID yang tepat")
        
        # Setup refresh token jika belum ada
        if not self.refresh_token:
            self.refresh_token = INITIAL_REFRESH_TOKEN
            if not self.refresh_token:
                print("[TOKEN] [ERROR] Refresh token tidak tersedia!")
                print("[TOKEN] [HINT] Set REFRESH_TOKEN env atau update session_data.json")
            else:
                print("[TOKEN] [INFO] Pakai refresh token dari env/config")

    def _save_to_cache(self):
        """Menyimpan token ke cache disk (backup) + Supabase (storage utama)"""
        try:
            profile = getattr(self, '_phone_profile', {})
            data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.expires_at,
                "app_instance_id": self.app_instance_id,
                "phone_profile": profile,
            }
            with open(self.cache_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[TOKEN] Gagal menyimpan cache: {e}")
        self._write_to_supabase()  # error sudah ditangani internal

    def _supabase_enabled(self) -> bool:
        """Apakah Supabase dikonfigurasi (URL + service role key)"""
        return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)

    def _read_from_supabase(self) -> dict | None:
        """Baca session dari Supabase. Return dict atau None jika kosong/gagal."""
        if not self._supabase_enabled():
            return None
        try:
            url = f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}?select=*&id=eq.default"
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=_supabase_headers())
            if resp.status_code == 200:
                rows = resp.json()
                if rows:
                    return rows[0]
            else:
                print(f"[TOKEN] [WARN] Supabase read status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[TOKEN] [WARN] Gagal baca dari Supabase: {e}")
        return None

    def _write_to_supabase(self):
        """Upsert session ke Supabase (single row id='default')."""
        if not self._supabase_enabled():
            return
        data = {
            "id": "default",
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "app_instance_id": self.app_instance_id,
            "phone_profile": getattr(self, '_phone_profile', {}) or None,
        }
        headers = {**_supabase_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"}
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}", json=data, headers=headers)
            if resp.status_code not in (200, 201):
                print(f"[TOKEN] [WARN] Supabase upsert status {resp.status_code}: {resp.text[:200]}")
        except Exception as e:
            print(f"[TOKEN] [WARN] Gagal tulis ke Supabase: {e}")

    def is_expired(self) -> bool:
        # Anggap expired 30 detik lebih awal agar aman
        return time.time() >= (self.expires_at - 30)

    async def refresh_token_v2(self) -> str:
        """Minta token baru menggunakan refresh_token (v2 Auth Flow)"""
        if not self.refresh_token:
            raise Exception("ERROR: Tidak ada refresh_token, tidak bisa ambil token baru")
        
        payload = {
            "app_instance_id": self.app_instance_id,  # Use fixed app instance ID
            "refresh_token": self.refresh_token,
        }

        headers = {
            **DEFAULT_HEADERS,
            "content-type": "application/json; charset=UTF-8",
        }

        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(REFRESH_TOKEN_URL, json=payload, headers=headers, timeout=15.0)
                    data = resp.json()

                if data.get("code") != 200:
                    error_msg = data.get("message", "Unknown error")
                    error_code = data.get("code")
                    
                    # Sesi TV Mandiri (Opsi 1 / Best Practice):
                    # Proxy punya sesi sendiri, terpisah dari HP. JANGAN PERNAH menyedot
                    # token HP saat error, karena akan menghidupkan kembali konflik rotasi!
                    is_standalone = (self._phone_profile.get("device_type") == "android_tv" 
                                     or os.environ.get("STANDALONE_AUTH", "1") == "1")

                    # Handle refresh_token_rotated — token dipake pihak lain duluan
                    if error_code == 401 and "rotated" in str(error_msg).lower():
                        print(f"[TOKEN] [ROTATED] Refresh token di-rotate: {error_msg}")
                        if is_standalone:
                            print("[TOKEN] [STANDALONE] Sesi mandiri TV perlu pairing ulang:")
                            print("[TOKEN] [HINT] Kunjungi: http://127.0.0.1:8000 → TV Device Pairing → Pair New TV Device")
                            raise Exception(f"Sesi mandiri expired/rotated. Buka dashboard di http://127.0.0.1:8000 dan klik 'Pair New TV Device'")
                        print("[TOKEN] [INFO] Coba extract token baru dari HP (legacy fallback)...")
                        try:
                            self._extract_from_phone()
                            payload["refresh_token"] = self.refresh_token
                            payload["app_instance_id"] = self.app_instance_id
                            async with httpx.AsyncClient() as client:
                                resp = await client.post(REFRESH_TOKEN_URL, json=payload, headers=headers, timeout=15.0)
                                data = resp.json()
                            if data.get("code") == 200:
                                token_info = data["data"]["token_info"]
                                self.access_token = token_info["access_token"]
                                self.refresh_token = token_info["refresh_token"]
                                expires_in = token_info.get("expires_in", 600)
                                self.expires_at = time.time() + expires_in
                                self._save_to_cache()
                                print(f"[TOKEN] [OK] Token dari HP (rotated recovery) berhasil, berlaku {expires_in} detik")
                                return self.access_token
                        except Exception as ex:
                            print(f"[TOKEN] [ERROR] Gagal extract dari HP (rotated recovery): {ex}")
                            print(f"[TOKEN] [HINT] Coba sambungkan HP via ADB dan restart server")
                    
                    # Handle expired/invalid token — extract dari HP (hanya jika mode legacy)
                    elif error_code == 401 and ("expired" in str(error_msg).lower() or "invalid" in str(error_msg).lower()):
                        print(f"[TOKEN] [ERROR] Refresh token expired/invalid: {error_msg}")
                        if is_standalone:
                            print("[TOKEN] [STANDALONE] Sesi mandiri TV expired. Kunjungi: http://127.0.0.1:8000 → TV Device Pairing")
                            raise Exception(f"Sesi TV expired. Buka dashboard di http://127.0.0.1:8000 dan klik 'Pair New TV Device'")
                        print("[TOKEN] [INFO] Coba extract token baru dari HP (legacy fallback)...")
                        try:
                            self._extract_from_phone()
                            # coba lagi dengan token baru dari HP
                            payload["refresh_token"] = self.refresh_token
                            payload["app_instance_id"] = self.app_instance_id
                            async with httpx.AsyncClient() as client:
                                resp = await client.post(REFRESH_TOKEN_URL, json=payload, headers=headers, timeout=15.0)
                                data = resp.json()
                            if data.get("code") == 200:
                                token_info = data["data"]["token_info"]
                                self.access_token = token_info["access_token"]
                                self.refresh_token = token_info["refresh_token"]
                                expires_in = token_info.get("expires_in", 600)
                                self.expires_at = time.time() + expires_in
                                self._save_to_cache()
                                print(f"[TOKEN] [OK] Token baru dari HP berhasil, berlaku {expires_in} detik")
                                return self.access_token
                        except Exception as ex:
                            print(f"[TOKEN] [ERROR] Gagal extract dari HP: {ex}")
                            print(f"[TOKEN] [HINT] Pastikan HP terhubung via ADB atau update token manual")
                    
                    # Untuk error lainnya, langsung throw
                    raise Exception(f"ERROR: Gagal refresh token: {error_msg} (code: {error_code})")

                # Success! Update token
                token_info = data["data"]["token_info"]
                self.access_token = token_info["access_token"]
                self.refresh_token = token_info["refresh_token"]  # Update refresh token (bisa berubah)
                expires_in = token_info.get("expires_in", 600)
                self.expires_at = time.time() + expires_in
                self._save_to_cache()

                print(f"[TOKEN] [OK] Token berhasil di-refresh independen, berlaku {expires_in} detik")
                return self.access_token
                
            except httpx.RequestError as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"[TOKEN] [WARN] Koneksi gagal (attempt {retry_count}/{max_retries}): {str(e)}")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                    continue
                else:
                    raise Exception(f"ERROR: Gagal refresh token setelah {max_retries} attempt: {str(e)}")
            except Exception as e:
                raise Exception(f"ERROR: {str(e)}")
        
        return self.access_token

    def _extract_from_phone(self):
        """Extract semua data auth dari HP via adb"""
        import subprocess
        import re
        
        adb_bin = os.environ.get("ADB_PATH", "adb")
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                cmd = [adb_bin, "shell", "run-as", "com.cineflow.app", "cat",
                       "/data/data/com.cineflow.app/shared_prefs/cineflow_primary_auth.xml"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    # Maybe adb server not ready, retry
                    if "no devices" in result.stderr.lower() or "daemon" in result.stderr.lower():
                        print(f"[TOKEN] [HP] adb not ready, retry {attempt+1}/{max_retries}...")
                        import time as _time
                        _time.sleep(2)
                        continue
                    raise Exception(f"adb error: {result.stderr}")
                
                xml = result.stdout
            except subprocess.TimeoutExpired:
                print(f"[TOKEN] [HP] timeout, retry {attempt+1}/{max_retries}...")
                import time as _time
                _time.sleep(2)
                continue
            except FileNotFoundError:
                raise Exception("adb tidak ditemukan. Install Android SDK platform-tools atau set ADB_PATH env.")
            break
        else:
            raise Exception(f"Gagal extract dari HP setelah {max_retries} percobaan")
        
        # Parse semua field dari XML
        fields = {
            "user_id": None,
            "email": None,
            "device_type": None,
            "refresh_token": None,
            "access_token": None,
            "app_instance_id": None,
        }
        for key in fields:
            m = re.search(rf'<string name="{key}">([^<]+)</string>', xml)
            if m:
                fields[key] = m.group(1)
        
        # Juga parse long values
        m_expires = re.search(r'<long name="access_token_expires_at_epoch_ms" value="(\d+)"', xml)
        m_refresh_expires = re.search(r'<long name="refresh_token_expires_at_epoch_ms" value="(\d+)"', xml)
        
        if not fields["refresh_token"]:
            raise Exception("refresh_token tidak ditemukan di data HP")
        
        # Simpan semua data
        self.refresh_token = fields["refresh_token"]
        self.access_token = fields["access_token"]
        self.app_instance_id = fields["app_instance_id"]
        
        # Simpan profile data untuk write-back nanti
        self._phone_profile = {
            "user_id": fields.get("user_id") or "usr_unknown",
            "email": fields.get("email") or "unknown@email.com",
            "device_type": fields.get("device_type") or "android_mobile",
            "app_instance_id": fields["app_instance_id"],
            "refresh_token_expires_at_epoch_ms": int(m_refresh_expires.group(1)) if m_refresh_expires else 0,
        }
        if m_expires:
            self.expires_at = int(m_expires.group(1)) / 1000
        
        print(f"[TOKEN] [HP] User: {self._phone_profile['email']}")
        print(f"[TOKEN] [HP] Instance: {self.app_instance_id[:12]}...")

    async def _write_to_phone_async(self):
        """Async version: write token ke HP via ADB (non-blocking)"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._write_to_phone)
        except Exception as e:
            print(f"[TOKEN] [WARN] Gagal sync ke HP (background): {e}")
            print(f"[TOKEN] [HINT] HP mungkin tidak terhubung via ADB. Token proxy tetap jalan.")

    def _write_to_phone(self):
        """Write current token back to phone via adb (biar HP gak logout)"""
        import subprocess
        import tempfile

        if not self.refresh_token or not self.access_token:
            return

        profile = getattr(self, '_phone_profile', {})
        user_id = profile.get("user_id") or "usr_597fc441c3165c45faa2"
        email = profile.get("email") or "watirena575@gmail.com"
        device_type = profile.get("device_type") or "android_mobile"
        # PENTING: pakai app_instance_id HP asli, bukan punya proxy. Kalau mismatch,
        # app HP akan re-register dan rotate refresh token → proxy logout.
        instance_id = profile.get("app_instance_id") or self.app_instance_id
        refresh_expires = profile.get("refresh_token_expires_at_epoch_ms") or int(self.expires_at * 1000) + (30 * 24 * 3600 * 1000)

        adb_bin = os.environ.get("ADB_PATH", "adb")

        try:
            expires_at_ms = int(self.expires_at * 1000) if self.expires_at else 0

            xml = f'''<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="access_token">{self.access_token}</string>
    <string name="refresh_token">{self.refresh_token}</string>
    <string name="user_id">{user_id}</string>
    <long name="refresh_token_expires_at_epoch_ms" value="{refresh_expires}" />
    <string name="app_instance_id">{instance_id}</string>
    <long name="access_token_expires_at_epoch_ms" value="{expires_at_ms}" />
    <string name="device_type">{device_type}</string>
    <string name="token_type">Bearer</string>
    <string name="email">{email}</string>
</map>'''

            # 1. Tulis XML ke temp file lokal
            tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False)
            tmp.write(xml)
            tmp.close()
            tmp_path = tmp.name

            # 2. Push ke /data/local/tmp (world-readable)
            device_tmp = "/data/local/tmp/cineflow_auth.xml"
            target = "/data/data/com.cineflow.app/shared_prefs/cineflow_primary_auth.xml"

            subprocess.run([adb_bin, "push", tmp_path, device_tmp],
                           capture_output=True, text=True, timeout=30)

            # 3. Copy via run-as (sumber readable, target app-private)
            subprocess.run([adb_bin, "shell", "run-as", "com.cineflow.app",
                           "cp", device_tmp, target],
                           capture_output=True, text=True, timeout=30)

            os.unlink(tmp_path)

            # 4. Force-stop app HP biar gak langsung refresh (race condition)
            #    Token baru sudah di-write, app akan baca pas dibuka lagi
            subprocess.run([adb_bin, "shell", "am", "force-stop", "com.cineflow.app"],
                           capture_output=True, text=True, timeout=10)

            print(f"[TOKEN] [HP] Token di-sync untuk {email} OK (instance {instance_id[:8]}...)")

        except subprocess.TimeoutExpired:
            print(f"[TOKEN] [WARN] Gagal sync ke HP: ADB timeout (HP tidak terhubung?)")
            print(f"[TOKEN] [HINT] Pastikan 'adb devices' menunjukkan device. Token proxy tetap jalan.")
        except FileNotFoundError:
            print(f"[TOKEN] [WARN] ADB tidak ditemukan. Install Android platform-tools atau set ADB_PATH env.")
            print(f"[TOKEN] [HINT] Token proxy tetap jalan, session HP mungkin logout saat token lama expired.")
        except Exception as e:
            print(f"[TOKEN] [WARN] Gagal sync ke HP: {e}")
            print(f"[TOKEN] [HINT] HP tidak terhubung? Token proxy tetap jalan, session HP mungkin logout saat token lama expired.")

    async def get_token(self) -> str:
        """Ambil token yang masih valid, atau minta baru jika expired.
        Cooldown 60s biar nggak spam refresh saat 429 / server sedang gencet."""
        if self.access_token is None or self.is_expired():
            now = time.time()
            if now - getattr(self, "_last_refresh_attempt", 0) < 60:
                if self.access_token:
                    return self.access_token
            self._last_refresh_attempt = now
            await self.refresh_token_v2()
        return self.access_token

# ============================================================
# Token Manager Instance
# ============================================================
token_manager = TokenManager()

# ============================================================
# Cache untuk endpoint proxy (path -> (expiry, content))
# ============================================================
_CACHE_TTL = 300  # 5 menit default
_CACHED_PATHS = ("models", "categories", "videos", "detail", "source")
# TTL khusus per-path atau per-provider/path (detik). Absen = pakai _CACHE_TTL.
_CACHE_TTL_OVERRIDES = {
    "source": 4 * 3600,  # default 4 jam (stream URL expire 5 jam)
}
# TTL per-provider untuk /source — hanya fallback untuk provider yang URL-nya
# TIDAK memakai auth_key=<timestamp> (provider ber-format auth_key ditangani
# otomatis oleh _extract_stream_ttl: TTL = sisa_expiry URL − 1 jam, cap 24 jam)
_CACHE_TTL_BY_PROVIDER_SOURCE = {
    "youku": 4 * 3600,           # 4 jam (stream expire 5 jam, format expire=18000)
}

def normalize_youku_streams(streams: list):
    """
    Koreksi pergeseran 1 tingkat resolusi Youku dari upstream server:
    cmfv4sd  (640x360 / 640x268)   -> 360p (bukan 480p)
    cmfv4hd  (864x486 / 864x362)   -> 480p (bukan 720p)
    cmfv4hd2 (1280x720 / 1280x536) -> 720p (bukan 1080p)
    cmfv4hd3 (1920x1080 / 1920x808)-> 1080p (bukan 4K)
    """
    if not isinstance(streams, list):
        return
    for s in streams:
        if not isinstance(s, dict):
            continue
        q_code = str(s.get("quality_code", "")).lower()
        url_str = str(s.get("url", "")) + " " + str(s.get("master_url", ""))
        q_orig = str(s.get("quality", "")).strip().lower()

        if q_code == "cmfv4hd3" or "type=cmfv4hd3" in url_str:
            s["quality"] = "1080p"
        elif q_code == "cmfv4hd2" or "type=cmfv4hd2" in url_str:
            s["quality"] = "720p"
        elif q_code == "cmfv4hd" or ("type=cmfv4hd" in url_str and "type=cmfv4hd2" not in url_str and "type=cmfv4hd3" not in url_str):
            s["quality"] = "480p"
        elif q_code == "cmfv4sd" or "type=cmfv4sd" in url_str:
            s["quality"] = "360p"
        elif q_code == "cmfv4ld" or "type=cmfv4ld" in url_str:
            s["quality"] = "240p"
        else:
            if q_orig == "4k":
                s["quality"] = "1080p"
            elif q_orig == "1080p":
                s["quality"] = "720p"
            elif q_orig == "720p":
                s["quality"] = "480p"
            elif q_orig == "480p":
                s["quality"] = "360p"
            elif q_orig == "360p":
                s["quality"] = "240p"

def _extract_stream_ttl(content):
    """
    Extract TTL dari response /source dengan parse auth_key=<unix_timestamp>-...
    Return: TTL dalam detik, dengan buffer -1 jam. Min 30 menit, max 24 jam.
    """
    try:
        if not isinstance(content, dict) or "data" not in content:
            return None
        
        data = content.get("data", {})
        if not isinstance(data, dict):
            return None
        
        streams = data.get("streams")
        if not isinstance(streams, list) or len(streams) == 0:
            return None
        
        url = streams[0].get("url", "")
        if not url or "auth_key=" not in url:
            return None
        
        # Parse auth_key parameter
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        auth_key_list = query_params.get("auth_key", [])
        
        if not auth_key_list:
            return None
        
        auth_key = auth_key_list[0]
        # Format: <unix_timestamp>-<hash>-<other>
        parts = auth_key.split("-")
        if len(parts) < 1:
            return None
        
        try:
            expiry_unix = int(parts[0])
        except ValueError:
            return None
        
        now = time.time()
        sisa_detik = expiry_unix - now
        
        # Buffer: kurangi 1 jam (3600 detik)
        buffer_detik = 3600
        ttl_detik = sisa_detik - buffer_detik
        
        # Min 30 menit, max 24 jam
        ttl_detik = max(1800, min(86400, ttl_detik))
        
        print(f"[CACHE TTL] Expiry: {expiry_unix}, sekarang: {now:.0f}, sisa: {sisa_detik:.0f}s, TTL final (−1h): {ttl_detik}s")
        return int(ttl_detik)
    
    except Exception as e:
        print(f"[CACHE TTL] Parse error: {e}")
        return None

def _ttl_for(path, model_id=None):
    # Jika path="source" dan ada model_id, gunakan TTL per-provider
    if path == "source" and model_id and model_id in _CACHE_TTL_BY_PROVIDER_SOURCE:
        return _CACHE_TTL_BY_PROVIDER_SOURCE[model_id]
    # Fallback ke override global atau default
    return _CACHE_TTL_OVERRIDES.get(path, _CACHE_TTL)

_models_cache = {}

# ============================================================
# Proxy Endpoint - Forward semua request ke ngintipya
# ============================================================
@app.api_route("/api/modelles/{path:path}", methods=["GET", "POST"],
    summary="Proxy untuk Content/Modelles API",
    description="Forward request ke `/api/modelles/*` CineFlow server. Auth token di-refresh otomatis jika expired.",
    tags=["Content & Streaming"],
    operation_id="proxy_modelles",
    responses={
        200: {"model": ProxyResponse, "description": "Success"},
        401: {"model": ErrorResponse, "description": "Token invalid"},
        500: {"model": ErrorResponse, "description": "Gagal ambil token"},
        502: {"model": ErrorResponse, "description": "Koneksi ke upstream gagal"},
    }
)
async def proxy(path: str, request: Request):
    """
    Proxy ke https://ngintipya2.cineflow.my.id/api/modelles/...
    Token Bearer diambil & di-refresh secara otomatis.
    """
    # 0. Block categories endpoint untuk WeTV, MovieBox & FreeReels
    if path == "categories" and request.method == "GET":
        model_id = request.query_params.get("model_id", "").lower()
        if model_id in ("wetv", "moviebox", "freereels"):
            print(f"[BLOCKED] categories for model_id={model_id}")
            return JSONResponse(
                content={"code": 403, "message": f"Categories untuk {model_id} tidak tersedia (gunakan API sendiri)", "status": "blocked"},
                status_code=403
            )

    # 1. Sajikan dari cache jika masih valid (hanya untuk GET)
    if request.method == "GET":
        cache_key = path
        # Untuk categories, tambahkan model_id ke cache key
        if path == "categories" and "model_id" in request.query_params:
            cache_key = f"{path}:{request.query_params['model_id']}"
        # Untuk videos, tambahkan model_id+category_id+page ke cache key
        elif path == "videos":
            model_id = request.query_params.get("model_id", "")
            category_id = request.query_params.get("category_id", "")
            page = request.query_params.get("page", "1")
            if model_id and category_id:
                cache_key = f"{path}:{model_id}:{category_id}:{page}"
        # Untuk detail, tambahkan model_id+id ke cache key
        elif path == "detail":
            model_id = request.query_params.get("model_id", "")
            content_id = request.query_params.get("id", "")
            if model_id and content_id:
                cache_key = f"{path}:{model_id}:{content_id}"
        # Untuk source, tambahkan model_id+id+episode_id ke cache key
        elif path == "source":
            model_id = request.query_params.get("model_id", "")
            content_id = request.query_params.get("id", "")
            episode_id = request.query_params.get("episode_id", "")
            if model_id and content_id and episode_id:
                cache_key = f"{path}:{model_id}:{content_id}:{episode_id}"
        
        cached = _models_cache.get(cache_key)
        if cached is not None and cached[0] > time.time():
            print(f"[CACHE HIT] {cache_key}")
            return JSONResponse(content=cached[1])

    # 1. Ambil token (otomatis refresh jika expired)
    try:
        token = await token_manager.get_token()
    except Exception as e:
        error_msg = str(e)
        print(f"[PROXY] ERROR: {error_msg}")
        return JSONResponse(
            content={"code": 500, "message": f"Gagal ambil session token: {error_msg}"},
            status_code=500,
        )

    # 2. Susun request ke target
    url = f"{TARGET_BASE_URL}/api/modelles/{path}"
    params = dict(request.query_params)
    headers = {
        **DEFAULT_HEADERS,
        "authorization": f"Bearer {token}",
    }

    # 2b. Ambil request body dan teruskan content-type jika ada (untuk POST search, dll)
    body = await request.body()
    if body and "content-type" in request.headers:
        headers["content-type"] = request.headers["content-type"]

    req_kwargs = {
        "method": request.method,
        "url": url,
        "params": params,
        "headers": headers,
        "timeout": 30.0,
    }
    if body:
        req_kwargs["content"] = body

    async with httpx.AsyncClient() as client:
        try:
            print(f"[PROXY] {request.method} {path}")
            response = await client.request(**req_kwargs)

            try:
                content = response.json()
            except Exception:
                content = {"raw": response.text}

            # 3. Jika 401, coba refresh token 1x lalu retry
            if response.status_code == 401 or content.get("code") == 401:
                print("[PROXY] 401 detected, refreshing token and retrying...")
                try:
                    token = await token_manager.refresh_token_v2()
                    headers["authorization"] = f"Bearer {token}"
                    req_kwargs["headers"] = headers

                    response = await client.request(**req_kwargs)
                    try:
                        content = response.json()
                    except Exception:
                        content = {"raw": response.text}
                except Exception as e:
                    print(f"[PROXY] ERROR: Gagal refresh token: {str(e)}")
                    return JSONResponse(
                        content={"code": 401, "message": f"Token refresh gagal: {str(e)}"},
                        status_code=401,
                    )

            # 4. Handle error responses dengan info lebih detail
            if response.status_code >= 500:
                error_detail = content.get("detail") or content.get("message") or "Unknown error"
                print(f"[PROXY] [ERROR] Server error {response.status_code}: {error_detail}")
            elif response.status_code >= 400:
                print(f"[PROXY] [WARN] Client error {response.status_code}")

            # Transform: rename "rating" -> "views" di response detail
            if path == "detail" and isinstance(content, dict):
                data = content.get("data")
                if isinstance(data, dict) and "rating" in data:
                    data["views"] = data.pop("rating")

            # Filter: hide WeTV, MovieBox & FreeReels dari /api/modelles/models
            if path == "models" and isinstance(content, dict):
                data = content.get("data")
                if isinstance(data, list):
                    content["data"] = [m for m in data if m.get("id") not in ("wetv", "moviebox", "freereels")]

            # Filter: hide news items (type="news") dari /api/modelles/videos
            if path == "videos" and isinstance(content, dict):
                data = content.get("data")
                if isinstance(data, dict) and "items" in data:
                    items = data["items"]
                    if isinstance(items, list):
                        data["items"] = [i for i in items if i.get("type") != "news"]

            # Normalisasi Stream Quality untuk Youku (koreksi pergeseran 1 tingkat dari upstream: 4K->1080p, 1080p->720p, 720p->480p, 480p->360p)
            if path == "source" and params.get("model_id", "").lower() == "youku" and isinstance(content, dict):
                data = content.get("data")
                if isinstance(data, dict):
                    streams = data.get("streams")
                    if isinstance(streams, list):
                        normalize_youku_streams(streams)

            # Simpan cache untuk endpoint yang di-cache
            if path in _CACHED_PATHS and request.method == "GET" and response.status_code == 200:
                cache_key = path
                # Untuk categories, tambahkan model_id ke cache key
                if path == "categories" and "model_id" in params:
                    cache_key = f"{path}:{params['model_id']}"
                # Untuk videos, tambahkan model_id+category_id+page ke cache key
                elif path == "videos":
                    model_id = params.get("model_id", "")
                    category_id = params.get("category_id", "")
                    page = params.get("page", "1")
                    if model_id and category_id:
                        cache_key = f"{path}:{model_id}:{category_id}:{page}"
                # Untuk detail, tambahkan model_id+id ke cache key
                elif path == "detail":
                    model_id = params.get("model_id", "")
                    content_id = params.get("id", "")
                    if model_id and content_id:
                        cache_key = f"{path}:{model_id}:{content_id}"
                # Untuk source, tambahkan model_id+id+episode_id ke cache key
                elif path == "source":
                    model_id = params.get("model_id", "")
                    content_id = params.get("id", "")
                    episode_id = params.get("episode_id", "")
                    if model_id and content_id and episode_id:
                        cache_key = f"{path}:{model_id}:{content_id}:{episode_id}"
                
                ttl = _ttl_for(path, params.get("model_id"))
                # Untuk /source, prioritaskan TTL dari expiry URL stream (−1 jam buffer),
                # agar cache tidak pernah melewati masa berlaku stream URL
                if path == "source":
                    stream_ttl = _extract_stream_ttl(content)
                    if stream_ttl is not None:
                        ttl = stream_ttl
                _models_cache[cache_key] = (time.time() + ttl, content)
                print(f"[CACHE SET] {cache_key} (TTL: {ttl}s)")

            return JSONResponse(content=content, status_code=response.status_code)

        except httpx.RequestError as exc:
            error_msg = str(exc)
            print(f"[PROXY] ERROR: Koneksi gagal: {error_msg}")
            return JSONResponse(
                content={"code": 502, "message": f"Koneksi ke upstream gagal: {error_msg}"},
                status_code=502,
            )
        except Exception as exc:
            error_msg = str(exc)
            print(f"[PROXY] ERROR: {error_msg}")
            return JSONResponse(
                content={"code": 500, "message": f"Error: {error_msg}"},
                status_code=500,
            )


# ============================================================
# Proxy Endpoint untuk /api/app/* (Account, Auth, Payment, dll)
# ============================================================
@app.api_route("/api/app/{path:path}", methods=["GET", "POST"],
    summary="Proxy untuk Account/Auth/Payment API",
    description="Forward request ke `/api/app/*` CineFlow server. Meliputi Account Status, Auth Me, Device Status, Payment Entitlement, Plans, Payment Status.",
    tags=["Account, Auth & Payment"],
    operation_id="proxy_app",
    responses={
        200: {"model": ProxyResponse, "description": "Success"},
        401: {"model": ErrorResponse, "description": "Token invalid"},
        500: {"model": ErrorResponse, "description": "Gagal ambil token"},
        502: {"model": ErrorResponse, "description": "Koneksi ke upstream gagal"},
    }
)
async def proxy_app(path: str, request: Request):
    """
    Proxy ke https://ngintipya2.cineflow.my.id/api/app/...
    Token Bearer diambil & di-refresh secara otomatis.
    """
    # 1. Ambil token (otomatis refresh jika expired)
    try:
        token = await token_manager.get_token()
    except Exception as e:
        error_msg = str(e)
        print(f"[PROXY-APP] ERROR: {error_msg}")
        return JSONResponse(
            content={"code": 500, "message": f"Gagal ambil session token: {error_msg}"},
            status_code=500,
        )

    # 2. Susun request ke target
    url = f"{TARGET_BASE_URL}/api/app/{path}"
    params = dict(request.query_params)
    headers = {
        **DEFAULT_HEADERS,
        "authorization": f"Bearer {token}",
    }

    # 2b. Ambil request body dan teruskan content-type jika ada
    body = await request.body()
    if body and "content-type" in request.headers:
        headers["content-type"] = request.headers["content-type"]

    req_kwargs = {
        "method": request.method,
        "url": url,
        "params": params,
        "headers": headers,
        "timeout": 30.0,
    }
    if body:
        req_kwargs["content"] = body

    async with httpx.AsyncClient() as client:
        try:
            print(f"[PROXY-APP] {request.method} {path}")
            response = await client.request(**req_kwargs)

            try:
                content = response.json()
            except Exception:
                content = {"raw": response.text}

            # 3. Jika 401, coba refresh token 1x lalu retry
            if response.status_code == 401 or content.get("code") == 401:
                print("[PROXY-APP] 401 detected, refreshing token and retrying...")
                try:
                    token = await token_manager.refresh_token_v2()
                    headers["authorization"] = f"Bearer {token}"
                    req_kwargs["headers"] = headers

                    response = await client.request(**req_kwargs)
                    try:
                        content = response.json()
                    except Exception:
                        content = {"raw": response.text}
                except Exception as e:
                    print(f"[PROXY-APP] ERROR: Gagal refresh token: {str(e)}")
                    return JSONResponse(
                        content={"code": 401, "message": f"Token refresh gagal: {str(e)}"},
                        status_code=401,
                    )

            # 4. Handle error responses
            if response.status_code >= 500:
                error_detail = content.get("detail") or content.get("message") or "Unknown error"
                print(f"[PROXY-APP] [ERROR] Server error {response.status_code}: {error_detail}")
            elif response.status_code >= 400:
                print(f"[PROXY-APP] [WARN] Client error {response.status_code}")

            return JSONResponse(content=content, status_code=response.status_code)

        except httpx.RequestError as exc:
            error_msg = str(exc)
            print(f"[PROXY-APP] ERROR: Koneksi gagal: {error_msg}")
            return JSONResponse(
                content={"code": 502, "message": f"Koneksi ke upstream gagal: {error_msg}"},
                status_code=502,
            )
        except Exception as exc:
            error_msg = str(exc)
            print(f"[PROXY-APP] ERROR: {error_msg}")
            return JSONResponse(
                content={"code": 500, "message": f"Error: {error_msg}"},
                status_code=500,
            )


# ============================================================
# MPD generator for bstation m4s (fMP4 with SegmentBase)
# ============================================================


@app.api_route("/api/v2/mpd", methods=["GET", "HEAD"], include_in_schema=False)
async def generate_mpd(video_url: str = "", audio_url: str = "", quality: str = ""):
    """Generate MPD XML for bstation fMP4 m4s files.
    Fetches m4s headers, parses moov/sidx ranges, returns MPD with SegmentBase."""
    from urllib.parse import quote
    if not video_url or not audio_url:
        return JSONResponse(content={"code": 400, "message": "Missing video_url or audio_url"}, status_code=400)

    client = _get_media_client()
    ref = "https://www.bilibili.tv/"
    base_hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": ref,
    }

    # Fetch video header (first 256KB). CDN bisa tolak (403 anti-leech) → pakai default ranges.
    vbuf = None
    vstat = "exc"
    try:
        vr = await client.get(video_url, headers={**base_hdrs, "Range": "bytes=0-262143"}, timeout=30)
        vstat = vr.status_code
        if vr.status_code in (200, 206):
            vbuf = vr.content
    except Exception as e:
        print(f"[MPD] video header EXC: {type(e).__name__}: {str(e)[:200]}")

    if vbuf and len(vbuf) >= 100:
        vinfo = _parse_m4s_header(vbuf)
    else:
        print(f"[MPD] WARN: video header gagal ({vstat}), pakai default ranges")
        vinfo = {}

    # Fetch audio header
    abuf = None
    astat = "exc"
    try:
        ar = await client.get(audio_url, headers={**base_hdrs, "Range": "bytes=0-262143"}, timeout=30)
        astat = ar.status_code
        if ar.status_code in (200, 206):
            abuf = ar.content
    except Exception as e:
        print(f"[MPD] audio header EXC: {type(e).__name__}: {str(e)[:200]}")

    if abuf and len(abuf) >= 100:
        ainfo = _parse_m4s_header(abuf)
    else:
        print(f"[MPD] WARN: audio header gagal ({astat}), pakai default ranges")
        ainfo = {}

    v_init_end = vinfo.get("moov_end", 928)
    v_sidx_start = vinfo.get("sidx_start", 929)
    v_sidx_end = vinfo.get("sidx_end", 3564)
    v_ts = vinfo.get("timescale", 16000)
    v_dur = vinfo.get("duration", 1080708)
    v_codec = vinfo.get("codec", "avc1")
    v_w = vinfo.get("width", 1920)
    v_h = vinfo.get("height", 1080)

    a_init_end = ainfo.get("moov_end", 817)
    a_sidx_start = ainfo.get("sidx_start", 818)
    a_sidx_end = ainfo.get("sidx_end", 3453)
    a_ts = ainfo.get("timescale", 48000)
    a_dur = ainfo.get("duration", 1080768)
    a_codec = ainfo.get("codec", "mp4a")

    dur_sec = max(v_dur / v_ts, a_dur / a_ts)
    dur_str = f"PT{dur_sec:.1f}S" if dur_sec > 0 else "PT0S"

    v_base = f"/media?url={quote(video_url, safe='')}&referer={quote(ref, safe='')}"
    a_base = f"/media?url={quote(audio_url, safe='')}&referer={quote(ref, safe='')}"

    mpd = f'''<?xml version="1.0" encoding="utf-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" profiles="urn:mpeg:dash:profile:isoff-live:2011" minBufferTime="PT2S" type="static" mediaPresentationDuration="{dur_str}">
  <Period>
    <AdaptationSet mimeType="video/mp4" contentType="video" segmentAlignment="true" startWithSAP="1">
      <Representation id="video" mimeType="video/mp4" codecs="{v_codec}" bandwidth="3000000" width="{v_w}" height="{v_h}">
        <BaseURL>{v_base}</BaseURL>
        <SegmentBase indexRange="{v_sidx_start}-{v_sidx_end - 1}" timescale="{v_ts}" presentationTimeOffset="0">
          <Initialization range="0-{v_init_end - 1}"/>
        </SegmentBase>
      </Representation>
    </AdaptationSet>
    <AdaptationSet mimeType="audio/mp4" contentType="audio" segmentAlignment="true" startWithSAP="1">
      <Representation id="audio" mimeType="audio/mp4" codecs="{a_codec}" bandwidth="128000">
        <BaseURL>{a_base}</BaseURL>
        <SegmentBase indexRange="{a_sidx_start}-{a_sidx_end - 1}" timescale="{a_ts}" presentationTimeOffset="0">
          <Initialization range="0-{a_init_end - 1}"/>
        </SegmentBase>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>'''

    return Response(content=mpd, media_type="application/dash+xml",
                    headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache"})


@app.get("/api/v2/subtitle", include_in_schema=False)
async def proxy_subtitle(url: str = ""):
    """Proxy subtitle files from CDN that require specific Referer headers."""
    if not url:
        return JSONResponse(content={"code": 400, "message": "Missing url"}, status_code=400)

    client = _get_media_client()
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Referer": "https://www.bilibili.tv/",
    }

    try:
        r = await client.get(url, headers=hdrs, timeout=30)
    except Exception as e:
        return JSONResponse(content={"code": 502, "message": f"Upstream error: {str(e)}"}, status_code=502)

    if r.status_code >= 400:
        return JSONResponse(content={"code": r.status_code, "message": "Upstream error"}, status_code=r.status_code)

    ct = r.headers.get("content-type", "text/plain")
    return Response(content=r.content, media_type=ct,
                    headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "public, max-age=3600"})


# ============================================================
# Adapter untuk frontend (format Supabase-style → CineFlow API)
# ============================================================
@app.api_route("/api/v2/{path:path}", methods=["GET", "POST"])
async def v2_adapter(path: str, request: Request):
    """
    Adapter frontend: terima request format lama (providers/sections/section-content),
    forward ke CineFlow API internal, transform response ke format yg frontend harapkan.
    """
    try:
        token = await token_manager.get_token()
    except Exception as e:
        return JSONResponse(content={"code": 500, "message": f"Gagal ambil session token: {str(e)}"}, status_code=500)

    async with httpx.AsyncClient() as client:
        base = TARGET_BASE_URL
        headers = {**DEFAULT_HEADERS, "authorization": f"Bearer {token}"}

        def fmt_ok(data, extra=None):
            r = {"code": 200, "message": "success", "status": "success", "data": data}
            if extra:
                r.update(extra)
            return r

        def do_get(url, params):
            return client.get(url, params=params, headers=headers, timeout=30.0)

        # ---- GET /providers → GET /api/modelles/models ----
        if path == "providers":
            resp = await do_get(f"{base}/api/modelles/models", {})
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            models = content.get("data") or []
            # Filter live_tv, map ke format frontend
            providers = []
            for m in models:
                if m.get("content_type") == "live_tv":
                    continue
                providers.append({
                    "id": m.get("id", ""),
                    "name": m.get("name", ""),
                    "status": m.get("status", "active"),
                    "icon_url": m.get("icon_url"),
                    "description": m.get("description"),
                    "content_type": m.get("content_type"),
                })
            return JSONResponse(content=fmt_ok(providers))

        # ---- GET /sections?provider=X → GET /api/modelles/categories?model_id=X ----
        if path == "sections":
            provider = request.query_params.get("provider", "")
            resp = await do_get(f"{base}/api/modelles/categories", {"model_id": provider})
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            data = content.get("data") or {}
            cats = data.get("data") if isinstance(data, dict) else []
            sections = []
            for c in cats or []:
                sections.append({
                    "title": c.get("name", ""),
                    "type": "CATEGORY",
                    "opId": c.get("id", ""),
                })
            return JSONResponse(content=fmt_ok(sections))

        # ---- GET /section-content?provider=X&opId=Y&page=N → GET /api/modelles/videos ----
        if path == "section-content":
            provider = request.query_params.get("provider", "")
            op_id = request.query_params.get("opId", "")
            page = request.query_params.get("page", "1")
            resp = await do_get(f"{base}/api/modelles/videos",
                                {"model_id": provider, "category_id": op_id, "page": page})
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            data = content.get("data") or {}
            items = data.get("items") if isinstance(data, dict) else []
            return JSONResponse(content=fmt_ok({"items": items, "pagination": None}))

        # ---- GET /search?q=X&provider=Y&page=N → POST /api/modelles/search ----
        if path == "search":
            q = request.query_params.get("q", "")
            provider = request.query_params.get("provider", "")
            page = int(request.query_params.get("page", "1"))
            content_type = request.query_params.get("content_type", "")
            body = {"q": q, "page": page}
            if provider and provider != "all":
                body["model_id"] = provider
            if content_type:
                body["content_type"] = content_type
            resp = await client.post(f"{base}/api/modelles/search", json=body, headers=headers, timeout=30.0)
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            data = content.get("data") or {}
            items = data.get("items") if isinstance(data, dict) else (data if isinstance(data, list) else [])
            # Map items: id = detailPath (valid untuk detail fetch), rating dari hot_score
            mapped = []
            for it in items or []:
                mapped.append({
                    **it,
                    "id": it.get("detailPath") or it.get("key") or it.get("id", ""),
                    "rating": it.get("rating") or (float(it["hot_score"]) if str(it.get("hot_score", "")).replace(".", "", 1).isdigit() else 0),
                    "cover": it.get("cover") or it.get("poster", ""),
                })
            return JSONResponse(content=fmt_ok({"items": mapped, "pagination": None}))

        # ---- GET /detail-content?id=X&provider=Y → GET /api/modelles/detail ----
        if path == "detail-content":
            provider = request.query_params.get("provider", "")
            content_id = request.query_params.get("id", "")
            resp = await do_get(f"{base}/api/modelles/detail",
                                {"model_id": provider, "id": content_id})
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            d = content.get("data") or {}
            raw_seasons = d.get("seasons") or []
            seen_seasons = {}
            dubs = {}
            for s in raw_seasons:
                idx = s.get("index", 1)
                ep_list = s.get("episodes") or []
                ep_numbers = [str(e.get("number", i + 1)) for i, e in enumerate(ep_list)]
                # Season: merge all_ep across same index
                if idx not in seen_seasons:
                    seen_seasons[idx] = {"all_eps": set(ep_numbers)}
                else:
                    seen_seasons[idx]["all_eps"].update(ep_numbers)
                # Dub: group by lang — clean name without season prefix
                lang = s.get("dubLang") or ""
                path = s.get("dubDetailPath") or s.get("dubSubjectId") or d.get("id", "")
                clean_name = s.get("name", "") or ""
                # Extract language from name e.g. "Season 1 (English dub)" -> "English dub"
                if "(" in clean_name and ")" in clean_name:
                    clean_name = clean_name.split("(", 1)[1].rsplit(")", 1)[0].strip()
                if lang not in dubs:
                    dubs[lang] = {
                        "subject_id": path,
                        "lan_code": lang,
                        "lan_name": clean_name,
                        "seasons": [],
                    }
                if idx not in dubs[lang]["seasons"]:
                    dubs[lang]["seasons"].append(idx)
            # Build season list
            seasons = []
            for idx in sorted(seen_seasons.keys()):
                info = seen_seasons[idx]
                all_ep = sorted(info["all_eps"], key=lambda x: int(x.split("-")[0]) if x.split("-")[0].isdigit() else 999)
                seasons.append({
                    "season_number": idx,
                    "episode_count": len(info["all_eps"]),
                    "all_ep": ",".join(all_ep),
                })
            dubs = list(dubs.values())
            views = str(d.get("views", ""))
            rating = 0.0
            try:
                rating = float(views)
            except (TypeError, ValueError):
                pass
            return JSONResponse(content=fmt_ok({
                "id": str(d.get("id", "")),
                "title": d.get("title", ""),
                "description": d.get("description", ""),
                "poster": d.get("cover_url", ""),
                "rating": rating,
                "content_type": "series",
                "genres": d.get("genres", []),
                "total_episodes": d.get("total_episodes", 0),
                "views": views,
                "seasons": seasons,
                "dubs": dubs,
            }))

        # ---- GET /episodes?id=X&provider=Y → flatten from modelles detail seasons ----
        if path == "episodes":
            provider = request.query_params.get("provider", "")
            content_id = request.query_params.get("id", "")
            resp = await do_get(f"{base}/api/modelles/detail",
                                {"model_id": provider, "id": content_id})
            content = resp.json()
            if content.get("code") != 200:
                return JSONResponse(content=content, status_code=resp.status_code)
            d = content.get("data") or {}
            # Filter to ONLY the dub matching the requested content_id
            # (raw detail returns all dubs' seasons mixed; path like money-heist-english-EWdtcM2bsU6
            #  or numeric dubSubjectId like 5800025460276973888)
            eps = []
            seen_ep_keys = set()
            for s in d.get("seasons") or []:
                if content_id not in (str(s.get("dubDetailPath", "")), str(s.get("dubSubjectId", ""))):
                    continue
                for e in s.get("episodes") or []:
                    ep_key = f"{s.get('index',1)}-{e.get('number',0)}"
                    if ep_key in seen_ep_keys:
                        continue
                    seen_ep_keys.add(ep_key)
                    eps.append({
                        "id": e.get("id", ""),
                        "content_id": s.get("dubSubjectId") or d.get("id", ""),
                        "season_number": s.get("index", 1),
                        "episode_number": e.get("number", 0),
                        "title": e.get("title", ""),
                        "thumbnail": e.get("thumbnail_url", ""),
                        "duration": e.get("duration_seconds", 0),
                        "is_vip": e.get("is_vip", False),
                    })
            return JSONResponse(content=fmt_ok(eps))

        # ---- GET /stream?id=X&provider=Y&season=S&episode=E&episode_id=ID → source ----
        if path == "stream":
            provider = request.query_params.get("provider", "")
            episode_id = request.query_params.get("episode_id", "")
            content_id = request.query_params.get("id", "")
            season = request.query_params.get("season", "1")
            episode = request.query_params.get("episode", "1")

            # If no episode_id provided, try to build from detail data
            if not episode_id:
                resp = await do_get(f"{base}/api/modelles/detail",
                                    {"model_id": provider, "id": content_id})
                detail = resp.json()
                if detail.get("code") == 200:
                    for s in (detail.get("data") or {}).get("seasons") or []:
                        if str(s.get("index")) == season:
                            for e in s.get("episodes") or []:
                                if str(e.get("number")) == episode:
                                    episode_id = e.get("id", "")
                                    break
                        if episode_id:
                            break

            if not episode_id:
                return JSONResponse(content={"code": 400, "message": "Cannot determine episode_id"}, status_code=400)

            src_resp = await do_get(f"{base}/api/modelles/source",
                                    {"model_id": provider, "episode_id": episode_id})
            src = src_resp.json()
            if src.get("code") != 200:
                return JSONResponse(content=src, status_code=src_resp.status_code)
            data = src.get("data", {})
            # Normalize bstation format: video[]/audio[] arrays → url pointing to MPD
            if data and isinstance(data, dict):
                streams = data.get("streams") or []
                if provider.lower() == "youku":
                    normalize_youku_streams(streams)
                for s in streams:
                    if not s.get("url") and s.get("video") and s.get("audio"):
                        from urllib.parse import quote as _q
                        vlist = s["video"]
                        alist = s["audio"]
                        vurl = vlist[0] if isinstance(vlist, list) and vlist else ""
                        aurl = alist[0] if isinstance(alist, list) and alist else ""
                        if vurl and aurl:
                            scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
                            host = request.headers.get("x-forwarded-host", request.url.netloc)
                            s["url"] = f"{scheme}://{host}/api/v2/mpd?video_url={_q(vurl, safe='')}&audio_url={_q(aurl, safe='')}&quality={_q(s.get('quality', ''), safe='')}"
                            s["format"] = "dash"
            return JSONResponse(content=fmt_ok(data))

        # ---- Fallback ----
        return JSONResponse(content={"code": 404, "message": f"Endpoint /api/v2/{path} belum diimplementasikan"}, status_code=404)

    return JSONResponse(content={"code": 500, "message": "Unexpected error"}, status_code=500)


_media_client: httpx.AsyncClient | None = None


def _get_media_client() -> httpx.AsyncClient:
    """Client persisten: koneksi pool reuse (hemat TCP+TLS handshake per request)."""
    global _media_client
    if _media_client is None:
        _media_client = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(120.0, connect=10.0, read=120.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )
    return _media_client


@app.api_route("/media", methods=["GET", "HEAD", "POST"], include_in_schema=False)
async def media_proxy(request: Request):
    """Stream proxy: forward ke CDN dengan Referer, dukung Range (seek video).
       Critical: pakai stream agar tak buffer file penuh (1.29GB movie!) di memory."""
    from fastapi.responses import StreamingResponse, Response
    from urllib.parse import quote
    target = request.query_params.get("url", "")
    referer = request.query_params.get("referer", "")
    cookie = request.query_params.get("cookie", "")
    if not target or not target.startswith("http"):
        return JSONResponse(content={"code": 400, "message": "Missing url param"}, status_code=400)

    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
        "Accept": "*/*",
    }
    if referer:
        hdrs["Referer"] = referer
    if cookie:
        hdrs["Cookie"] = cookie

    range_hdr = request.headers.get("range")
    fwd_hdrs = dict(hdrs)
    if range_hdr:
        fwd_hdrs["Range"] = range_hdr

    client = _get_media_client()

    if request.method == "HEAD":
        try:
            upstream = await client.head(target, headers=fwd_hdrs, timeout=30.0)
        except Exception as e:
            return JSONResponse(content={"code": 502, "message": f"Upstream error: {str(e)}"}, status_code=502)
        if upstream.status_code >= 400:
            return JSONResponse(content={"code": upstream.status_code, "message": "Upstream error"}, status_code=upstream.status_code)
        resp_headers = {}
        for h in ("content-type", "content-length", "content-range", "accept-ranges", "etag", "cache-control"):
            v = upstream.headers.get(h)
            if v:
                resp_headers[h] = v
        resp_headers["Access-Control-Allow-Origin"] = "*"
        ct = upstream.headers.get("content-type", "").lower()
        is_dash = ("dash+xml" in ct) or ".mpd" in target or ".mpd?" in target
        if is_dash:
            resp_headers["content-type"] = "application/dash+xml"
        return Response(status_code=upstream.status_code, headers=resp_headers)

    # POST: forward license/DRM requests (e.g Youku license)
    if request.method == "POST":
        try:
            body = await request.body()
            upstream = await client.post(target, content=body, headers=fwd_hdrs, timeout=30.0)
        except Exception as e:
            return JSONResponse(content={"code": 502, "message": f"Upstream error: {str(e)}"}, status_code=502)
        if upstream.status_code >= 400:
            return JSONResponse(content={"code": upstream.status_code, "message": "Upstream error"}, status_code=upstream.status_code)
        resp_headers = {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": upstream.headers.get("content-type", "application/octet-stream"),
        }
        return Response(content=upstream.content, status_code=upstream.status_code, headers=resp_headers)

    # GET: stream agar tak buffer penuh file video
    try:
        req = client.build_request("GET", target, headers=fwd_hdrs)
        upstream = await client.send(req, stream=True)
    except Exception as e:
        return JSONResponse(content={"code": 502, "message": f"Upstream error: {str(e)}"}, status_code=502)
    if upstream.status_code >= 400:
        return JSONResponse(content={"code": upstream.status_code, "message": "Upstream error"}, status_code=upstream.status_code)

    ct = upstream.headers.get("content-type", "").lower()
    is_dash = ("dash+xml" in ct) or ".mpd" in target or ".mpd?" in target

    resp_headers = {}
    for h in ("content-type", "content-length", "content-range", "accept-ranges", "etag", "cache-control"):
        v = upstream.headers.get(h)
        if v:
            resp_headers[h] = v
    resp_headers["Access-Control-Allow-Origin"] = "*"

    # ---- DASH MPD: rewrite segment URLs so they go through this proxy (need Referer) ----
    if is_dash:
        try:
            import re
            raw = await upstream.aread()
            text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            base = target.rsplit("/", 1)[0] + "/"

            def wrap(u: str) -> str:
                u = u.strip()
                if not u or u.startswith("data:") or u.startswith("#"):
                    return u
                if u.startswith("/media?"):
                    return u
                abs_u = u if u.startswith("http") else (base + u)
                ck = f"&cookie={quote(cookie, safe='')}" if cookie else ""
                parts = re.split(r'(\$[A-Za-z]+(?:%0\d+d)?\$)', abs_u)
                encoded_u = ''.join(quote(p, safe='') if not p.startswith('$') else p for p in parts)
                return f"/media?url={encoded_u}&referer={quote(referer, safe='')}{ck}"

            text = re.sub(r'<BaseURL[^>]*>([^<]*)</BaseURL>',
                          lambda m: f'<BaseURL>{wrap(m.group(1))}</BaseURL>', text)
            text = re.sub(r'(<SegmentTemplate[^>]*media=")([^"]+)(")',
                          lambda m: m.group(1) + wrap(m.group(2)) + m.group(3), text)
            text = re.sub(r'(<SegmentTemplate[^>]*initialization=")([^"]+)(")',
                          lambda m: m.group(1) + wrap(m.group(2)) + m.group(3), text)
            text = re.sub(r'(<SegmentURL[^>]*media=")([^"]+)(")',
                          lambda m: m.group(1) + wrap(m.group(2)) + m.group(3), text)
            text = re.sub(r'(<Initialization[^>]*sourceURL=")([^"]+)(")',
                          lambda m: m.group(1) + wrap(m.group(2)) + m.group(3), text)

            resp_headers = {
                "Content-Type": "application/dash+xml",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            }
            return Response(text, status_code=200, headers=resp_headers)
        except Exception as e:
            return JSONResponse(content={"code": 500, "message": f"MPD rewrite error: {str(e)}"}, status_code=500)

    # ---- HLS m3u8: rewrite segment URLs so they go through this proxy (no CORS on CDN) ----
    is_hls = (".m3u8" in target) or ("mpegurl" in ct) or ("hls" in ct and "mpd" not in ct)
    if is_hls:
        try:
            import re
            raw = await upstream.aread()
            text = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            base = target.rsplit("/", 1)[0] + "/"

            def wrap_hls(u: str) -> str:
                u = u.strip()
                if not u or u.startswith("#") or u.startswith("data:"):
                    return u
                if u.startswith("/media?"):
                    return u
                abs_u = u if u.startswith("http") else (base + u)
                ck = f"&cookie={quote(cookie, safe='')}" if cookie else ""
                return f"/media?url={quote(abs_u, safe='')}&referer={quote(referer, safe='')}{ck}"

            lines = []
            for ln in text.splitlines():
                s = ln.strip()
                # Rewrite only segment URIs (not #EXT headers, not #EXT-X-KEY/MAP URIs)
                if s and not s.startswith("#") and not s.startswith("//"):
                    lines.append(wrap_hls(s))
                else:
                    lines.append(ln)
            text = "\n".join(lines)

            resp_headers = {
                "Content-Type": "application/vnd.apple.mpegurl",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            }
            return Response(text, status_code=200, headers=resp_headers)
        except Exception as e:
            return JSONResponse(content={"code": 500, "message": f"HLS rewrite error: {str(e)}"}, status_code=500)

    # ---- MP4 / non-DASH: stream bytes langsung (tak buffer penuh) ----
    async def iter_chunks():
        try:
            async for chunk in upstream.aiter_bytes(chunk_size=65536):
                yield chunk
        finally:
            await upstream.aclose()

    return StreamingResponse(
        iter_chunks(),
        status_code=upstream.status_code,
        headers=resp_headers,
    )


# ============================================================
# MPD generator for bstation m4s (fMP4 with SegmentBase)
# ============================================================


def _parse_boxes(buf, offset, end):
    boxes = []
    while offset + 8 <= end:
        size = struct.unpack(">I", buf[offset:offset+4])[0]
        btype = buf[offset+4:offset+8].decode("latin1")
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", buf[offset+8:offset+16])[0]
            hdr = 16
        elif size == 0:
            size = end - offset
        if size < hdr or offset + size > end:
            break
        boxes.append((offset, size, btype, hdr))
        offset += size
    return boxes


def _find_box_chain(buf, *targets, start=0, end=None):
    """Find nested box by path, e.g. _find_box_chain(buf, 'moov', 'mvhd')"""
    pos = start
    limit = end or len(buf)
    for tgt in targets:
        found = False
        for off, size, bt, hdr in _parse_boxes(buf, pos, limit):
            if bt == tgt:
                pos = off + hdr
                limit = off + size
                found = True
                break
        if not found:
            return None, None
    return pos, limit


def _parse_m4s_header(buf):
    """Parse fMP4 header bytes → dict with moov_end, sidx ranges, timescale, codec, dims"""
    result = {}
    boxes = _parse_boxes(buf, 0, len(buf))
    for off, size, bt, hdr in boxes:
        if bt == "moov":
            result["moov_end"] = off + size
        elif bt == "sidx":
            result["sidx_start"] = off
            result["sidx_end"] = off + size
    # mvhd → timescale + duration
    mvhd_pos, mvhd_end = _find_box_chain(buf, "moov", "mvhd")
    if mvhd_pos:
        v = buf[mvhd_pos]
        p = mvhd_pos + 4
        if v == 1:
            ts = struct.unpack(">I", buf[p+16:p+20])[0]
            dur = struct.unpack(">Q", buf[p+20:p+28])[0]
        else:
            ts = struct.unpack(">I", buf[p+8:p+12])[0]
            dur = struct.unpack(">I", buf[p+12:p+16])[0]
        result["timescale"] = ts
        result["duration"] = dur
    # tkhd → width/height
    tkhd_pos, tkhd_end = _find_box_chain(buf, "moov", "trak", "tkhd")
    if tkhd_pos:
        v = buf[tkhd_pos]
        p = tkhd_pos + 4
        if v == 1:
            p += 80
        else:
            p += 64
        p += 36
        w = struct.unpack(">I", buf[p:p+4])[0] >> 16
        h = struct.unpack(">I", buf[p+4:p+8])[0] >> 16
        result["width"] = w
        result["height"] = h
    # stsd → codec
    stsd_pos, stsd_end = _find_box_chain(buf, "moov", "trak", "mdia", "minf", "stbl", "stsd")
    if stsd_pos:
        p = stsd_pos + 8
        if p + 8 <= len(buf):
            result["codec"] = buf[p+4:p+8].decode("latin1")
    return result







# ============================================================
# TV Device Pairing Endpoints (Device-Code Flow)
# ============================================================

@app.post("/api/auth/pair/init",
    summary="Mulai TV device pairing",
    description="Generate pairing code untuk TV device. User buka verification_url di browser HP/PC, login, lalu approve.",
    tags=["TV Pairing"],
    response_model=PairInitResponse,
    responses={500: {"model": ErrorResponse}})
async def pair_init():
    """Mulai device pairing flow. Return device_code, user_code, verification_url."""
    try:
        app_instance_id = str(uuid.uuid4())
        
        body = {
            "app_instance_id": app_instance_id,
            "device_type": TV_DEVICE_INFO["device_type"],
            "ui_mode": TV_DEVICE_INFO["ui_mode"],
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                PAIRING_URL,
                json=body,
                headers=DEFAULT_HEADERS,
                timeout=15.0
            )
            data = resp.json()
        
        if data.get("code") != 200:
            error_msg = data.get("message", "Unknown error")
            return JSONResponse(
                content={"code": 500, "message": f"Pairing init gagal: {error_msg}"},
                status_code=500,
            )
        
        pairing_data = data.get("data", {})
        return {
            "code": 200,
            "message": "Pairing code generated. Buka verification_url di browser HP/PC, login, lalu approve.",
            "data": {
                "device_code": pairing_data.get("device_code"),
                "user_code": pairing_data.get("user_code"),
                "verification_uri": pairing_data.get("verification_uri"),
                "verification_uri_complete": pairing_data.get("verification_uri_complete"),
                "expires_in_seconds": pairing_data.get("expires_in_seconds", 900),
                "interval_seconds": pairing_data.get("interval_seconds", 5),
                "_app_instance_id": app_instance_id,  # internal: simpan untuk poll
            }
        }
    
    except Exception as e:
        return JSONResponse(
            content={"code": 500, "message": f"Error: {str(e)}"},
            status_code=500,
        )


@app.get("/api/auth/pair/poll",
    summary="Poll TV pairing status",
    description="Poll approval status. Jika approved, tukar grant_token → access_token + refresh_token dan auto-save.",
    tags=["TV Pairing"],
    response_model=PairPollResponse,
    responses={202: {"model": PairPollResponse}, 500: {"model": ErrorResponse}})
async def pair_poll(device_code: str, app_instance_id: str):
    """Poll pairing status. Jika approved: exchange token + save ke session."""
    try:
        params = {
            "device_code": device_code,
            "app_instance_id": app_instance_id,
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                PAIRING_STATUS_URL,
                params=params,
                headers=DEFAULT_HEADERS,
                timeout=15.0
            )
            data = resp.json()
        
        if data.get("code") != 200:
            error_msg = data.get("message", "Unknown error")
            return JSONResponse(
                content={"code": 500, "message": f"Poll status gagal: {error_msg}"},
                status_code=500,
            )
        
        status_data = data.get("data", {})
        is_approved = status_data.get("approved", False)
        grant_token = status_data.get("grant_token")
        
        # Masih pending approval
        if not is_approved or not grant_token:
            return JSONResponse(
                content={
                    "code": 202,
                    "message": "Waiting for approval...",
                    "data": {
                        "status": status_data.get("status", "pending"),
                        "approved": is_approved,
                        "interval_seconds": status_data.get("interval_seconds", 5),
                    }
                },
                status_code=202,
            )
        
        # Approved! Exchange token
        exchange_body = {
            "grant_token": grant_token,
            "app_instance_id": app_instance_id,
            **{k: v for k, v in TV_DEVICE_INFO.items() if k not in ["app_version_code", "app_version_name"]},
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                PAIRING_EXCHANGE_URL,
                json=exchange_body,
                headers=DEFAULT_HEADERS,
                timeout=15.0
            )
            ex_data = resp.json()
        
        if ex_data.get("code") != 200:
            error_msg = ex_data.get("message", "Unknown error")
            return JSONResponse(
                content={"code": 500, "message": f"Token exchange gagal: {error_msg}"},
                status_code=500,
            )
        
        # Success! Update token manager + save
        ex_result = ex_data.get("data", {})
        token_info = ex_result.get("token_info", {})
        user = ex_result.get("user", {})
        
        token_manager.access_token = token_info.get("access_token")
        token_manager.refresh_token = token_info.get("refresh_token")
        expires_in = int(token_info.get("expires_in", 600))
        token_manager.expires_at = time.time() + expires_in
        token_manager.app_instance_id = app_instance_id
        
        # Update phone profile untuk tracking (TV device)
        token_manager._phone_profile = {
            "user_id": user.get("id"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "google_sub": user.get("google_sub"),
            "device_type": "android_tv",
            "app_instance_id": app_instance_id,
            "provider": user.get("provider", "google"),
            "linked_at": user.get("linked_at"),
        }
        
        token_manager._save_to_cache()
        
        return {
            "code": 200,
            "message": "Pairing successful! Token saved dan proxy siap dipakai.",
            "data": {
                "access_token": token_info.get("access_token")[:30] + "...",
                "refresh_token": token_info.get("refresh_token")[:30] + "...",
                "expires_in_seconds": expires_in,
                "user_email": user.get("email"),
                "instance_id": app_instance_id,
            }
        }
    
    except Exception as e:
        return JSONResponse(
            content={"code": 500, "message": f"Error: {str(e)}"},
            status_code=500,
        )


@app.get("/", response_class=HTMLResponse,
    summary="Dashboard UI",
    description="Halaman dashboard interaktif dengan status token, setup, daftar endpoint, dan API tester.",
    tags=["Dashboard"],
    include_in_schema=False)
async def root():
    """Tampilkan Dashboard"""
    token_preview = "NO TOKEN"
    expires_in = 0
    is_expired = True
    error_msg = None
    profile = {}
    
    try:
        token = await token_manager.get_token()
        remaining = max(0, token_manager.expires_at - time.time())
        token_preview = token[:40] + "..."
        expires_in = round(remaining)
        is_expired = token_manager.is_expired()
        profile = getattr(token_manager, '_phone_profile', {})
    except Exception as e:
        error_msg = str(e)
        print(f"[DASHBOARD] ERROR: {error_msg}")
    
    return get_dashboard_html(
        token_preview=token_preview,
        expires_in=expires_in,
        is_expired=is_expired,
        error_msg=error_msg,
        profile=profile
    )


@app.get("/api/user/profile",
    summary="User Account Profile",
    description="Mengembalikan data profil user akun yang sedang aktif/tersimpan.",
    tags=["Account"])
async def user_profile():
    """Endpoint untuk mendapatkan profil pengguna"""
    profile = getattr(token_manager, '_phone_profile', {})
    is_logged_in = token_manager.refresh_token is not None
    return {
        "code": 200,
        "message": "User profile retrieved successfully",
        "data": {
            "email": profile.get("email"),
            "user_id": profile.get("user_id"),
            "display_name": profile.get("display_name"),
            "device_type": profile.get("device_type"),
            "provider": profile.get("provider", "google"),
            "linked_at": profile.get("linked_at"),
            "app_instance_id": token_manager.app_instance_id,
            "is_logged_in": is_logged_in,
            "is_token_expired": token_manager.is_expired()
        }
    }


@app.get("/api/token/status",
    summary="Cek status token",
    description="Lihat informasi token saat ini: apakah ada, preview, expiry, dan status refresh token.",
    tags=["Token Management"],
    response_model=TokenStatusResponse)
async def token_status():
    """Endpoint untuk mengecek status token saat ini"""
    remaining = max(0, token_manager.expires_at - time.time())
    return {
        "has_token": token_manager.access_token is not None,
        "has_refresh_token": token_manager.refresh_token is not None,
        "token_preview": (token_manager.access_token[:20] + "...") if token_manager.access_token else None,
        "expires_in_seconds": round(remaining),
        "is_expired": token_manager.is_expired(),
        "refresh_token_preview": (token_manager.refresh_token[:20] + "...") if token_manager.refresh_token else None,
    }


@app.post("/api/token/set",
    summary="Set token baru (POST)",
    description="Set refresh token baru via POST JSON body. Server akan auto-refresh dan menyimpan token.",
    tags=["Token Management"],
    response_model=TokenSetResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
async def set_token(request: Request):
    """
    Endpoint untuk set token secara manual.
    Body: {"refresh_token": "cf_rt_..."}
    """
    try:
        data = await request.json()
        refresh_token = data.get("refresh_token")
        
        if not refresh_token:
            return JSONResponse(
                content={"code": 400, "message": "refresh_token diperlukan di body"},
                status_code=400,
            )
        
        token_manager.refresh_token = refresh_token
        # Clear access token agar refresh baru
        token_manager.access_token = None
        token_manager.expires_at = 0
        
        # Coba refresh token baru
        try:
            token = await token_manager.refresh_token_v2()
            return {
                "code": 200,
                "message": "Token berhasil diset dan di-refresh",
                "token_preview": token[:20] + "...",
                "expires_in_seconds": int(token_manager.expires_at - time.time())
            }
        except Exception as e:
            return JSONResponse(
                content={"code": 500, "message": f"Gagal refresh dengan token baru: {str(e)}"},
                status_code=500,
            )
    
    except Exception as e:
        return JSONResponse(
            content={"code": 500, "message": f"Error: {str(e)}"},
            status_code=500,
        )


@app.post("/api/token/refresh",
    summary="Paksa refresh token",
    description="Paksa server untuk me-refresh access token menggunakan refresh_token yang tersimpan.",
    tags=["Token Management"],
    response_model=TokenRefreshResponse,
    responses={500: {"model": ErrorResponse}})
async def force_refresh():
    """Paksa refresh token secara manual"""
    try:
        token = await token_manager.refresh_token_v2()
        return {"code": 200, "message": "Token refreshed", "token_preview": token[:20] + "..."}
    except Exception as e:
        return JSONResponse(
            content={"code": 500, "message": str(e)},
            status_code=500,
        )


@app.get("/api/token/set",
    summary="Set token baru (GET)",
    description="Set refresh token baru via GET parameter. Mudah diakses dari HP browser.",
    tags=["Token Management"],
    include_in_schema=True)
async def set_token_get(refresh_token: str = ""):
    """Set token via GET parameter (mudah akses dari HP browser)"""
    if not refresh_token or not refresh_token.startswith("cf_rt_"):
        return HTMLResponse(f"""
        <html><body style="background:#0f172a;color:#f1f5f9;font-family:sans-serif;padding:40px;text-align:center">
        <h2>❌ Token invalid</h2>
        <p>refresh_token harus dimulai dengan <code>cf_rt_</code></p>
        <p>Gunakan: <code>/api/token/set?refresh_token=cf_rt_...</code></p>
        </body></html>""")
    
    token_manager.refresh_token = refresh_token
    token_manager.access_token = None
    token_manager.expires_at = 0
    
    try:
        token = await token_manager.refresh_token_v2()
        return HTMLResponse(f"""
        <html><body style="background:#0f172a;color:#f1f5f9;font-family:sans-serif;padding:40px;text-align:center">
        <h2>✅ Token berhasil diset!</h2>
        <p>Proxy akan auto-refresh selamanya.</p>
        <p><a href="/" style="color:#38bdf8;">← Back to Dashboard</a></p>
        </body></html>""")
    except Exception as e:
        return HTMLResponse(f"""
        <html><body style="background:#0f172a;color:#f1f5f9;font-family:sans-serif;padding:40px;text-align:center">
        <h2>❌ Gagal refresh</h2>
        <p>{str(e)}</p>
        <p>Token mungkin sudah dipakai/expired. Coba ambil token baru.</p>
        </body></html>""")

@app.get("/api/token/info",
    summary="Token info lengkap (mobile-friendly)",
    include_in_schema=False)
async def token_info_page():
    """Halaman HTML mobile-friendly dengan semua info token"""
    remaining = max(0, token_manager.expires_at - time.time())
    is_expired = token_manager.is_expired()
    
    access_token = token_manager.access_token or "N/A"
    refresh_token = token_manager.refresh_token or "N/A"
    instance_id = token_manager.app_instance_id or "N/A"
    profile = getattr(token_manager, '_phone_profile', {})
    email = profile.get("email") or "unknown"
    user_id = profile.get("user_id") or "unknown"
    
    expires_str = f"{round(remaining)} detik"
    if remaining > 86400:
        expires_str = f"{round(remaining/86400)} hari"
    elif remaining > 3600:
        expires_str = f"{round(remaining/3600)} jam"
    
    return HTMLResponse(f"""
    <!DOCTYPE html><html><head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
    <title>Token Info</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family:'Segoe UI',sans-serif; background:#0f172a; color:#f1f5f9; padding:16px; }}
        h1 {{ font-size:1.3rem; margin:16px 0; color:#38bdf8; }}
        .card {{ background:#1e293b; border-radius:12px; padding:16px; margin-bottom:12px; border:1px solid rgba(255,255,255,0.05); }}
        .label {{ font-size:0.7rem; color:#64748b; margin-bottom:4px; }}
        .value {{ font-family:'Courier New',monospace; font-size:0.75rem; color:#a5d6ff; word-break:break-all; background:#00000033; padding:8px; border-radius:6px; }}
        .badge {{ display:inline-block; padding:2px 8px; border-radius:10px; font-size:0.7rem; font-weight:600; }}
        .badge.ok {{ background:#10b98122; color:#10b981; }}
        .badge.err {{ background:#ef444422; color:#ef4444; }}
        .copy-btn {{ background:#38bdf8; color:#0f172a; border:none; padding:6px 12px; border-radius:6px; font-weight:600; cursor:pointer; margin-top:6px; font-size:0.75rem; }}
        a {{ color:#38bdf8; text-decoration:none; }}
    </style>
    <script>
    function copyText(id) {{
        const el = document.getElementById(id);
        const text = el.innerText;
        const doCopy = (btn) => {{
            btn.innerText = '✅ Copied!';
            setTimeout(() => btn.innerText = '📋 Copy', 2000);
        }};
        if (navigator.clipboard) {{
            navigator.clipboard.writeText(text).then(() => {{
                doCopy(el.parentElement.querySelector('.copy-btn'));
            }}).catch(() => fallbackCopyText(el, text));
        }} else {{
            fallbackCopyText(el, text);
        }}
    }}

    function fallbackCopyText(el, text) {{
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {{
            document.execCommand('copy');
            const btn = el.parentElement.querySelector('.copy-btn');
            btn.innerText = '✅ Copied!';
            setTimeout(() => btn.innerText = '📋 Copy', 2000);
        }} catch (e) {{
            alert('Copy gagal. Select manual.');
        }} finally {{
            document.body.removeChild(textarea);
        }}
    }}
    </script></head><body>
    <h1>🔑 Token Info <span class="badge {'ok' if not is_expired else 'err'}">{'Active' if not is_expired else 'Expired'}</span></h1>
    <div class="card"><div class="label">Email</div><div class="value">{email}</div></div>
    <div class="card"><div class="label">User ID</div><div class="value" id="uid">{user_id}</div><button class="copy-btn" onclick="copyText('uid')">📋 Copy</button></div>
    <div class="card"><div class="label">App Instance ID</div><div class="value" id="iid">{instance_id}</div><button class="copy-btn" onclick="copyText('iid')">📋 Copy</button></div>
    <div class="card"><div class="label">Access Token</div><div class="value" id="at">{access_token}</div><button class="copy-btn" onclick="copyText('at')">📋 Copy</button></div>
    <div class="card"><div class="label">Refresh Token</div><div class="value" id="rt">{refresh_token}</div><button class="copy-btn" onclick="copyText('rt')">📋 Copy</button></div>
    <div class="card"><div class="label">Expires</div><div class="value">{expires_str}</div></div>
    <div style="text-align:center;font-size:0.75rem;color:#64748b;margin-top:16px;">
        <p><a href="/">← Back to Dashboard</a></p>
    </div>
    </body></html>
    """)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 6101))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"[CINEFLOW] Proxy v{app.version} — http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=False)
