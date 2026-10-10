import os

# Clean up NO_PROXY environment variable to prevent HTTPX from crashing on raw IPv6 loopback addresses like ::1
no_proxy = os.environ.get("NO_PROXY", "")
if no_proxy:
    parts = [p.strip() for p in no_proxy.split(",")]
    cleaned_parts = [p for p in parts if not (":" in p and not (p.startswith("[") and "]" in p))]
    os.environ["NO_PROXY"] = ",".join(cleaned_parts)

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("viu-proxy.main")

# Import modular routers
from dotenv import load_dotenv
load_dotenv()

from config import router as config_router
from home import router as home_router
from play import router as play_router
from category import router as category_router
from auth import router as auth_router

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize shared HTTPX AsyncClient
    logger.info("Initializing async HTTPX client connection pool...")
    app.state.http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
        verify=True
    )
    yield
    # Shutdown: Close connection pool
    logger.info("Closing async HTTPX client...")
    await app.state.http_client.aclose()

# Create FastAPI app instance
app = FastAPI(
    title="Viu API Gateway Real-Time Reverse Proxy",
    description="High-performance, modular reverse proxy for Viu API endpoints.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse

# Bearer Auth middleware — aktif jika API_SECRET_KEY diatur di .env
@app.middleware("http")
async def api_secret_auth_middleware(request: Request, call_next):
    # Selalu loloskan pre-flight OPTIONS
    if request.method == "OPTIONS":
        return await call_next(request)

    secret_key = os.getenv("API_SECRET_KEY", "").strip()
    dashboard_path = os.getenv("DASHBOARD_SECRET_PATH", "/admin/dashboard").strip()

    # Jika secret key diisi, proteksi semua endpoint kecuali dashboard rahasia
    if secret_key:
        path = request.url.path

        # Loloskan dashboard rahasia
        if path == dashboard_path:
            return await call_next(request)

        # Loloskan request yg berasal dari halaman dashboard (fetch internal JS tanpa Bearer)
        referer = request.headers.get("referer", "")
        if dashboard_path and dashboard_path in referer:
            return await call_next(request)

        # Cek Header Authorization: Bearer <token>
        auth_header = request.headers.get("authorization", "")
        token_from_header = auth_header.split(" ", 1)[1].strip() if auth_header.startswith("Bearer ") else ""

        # Cek Query Parameter ?api_key=<token> atau ?secret=<token> (khusus request media player / m3u8)
        token_from_query = request.query_params.get("api_key") or request.query_params.get("secret")

        authorized = (token_from_header == secret_key) or (token_from_query == secret_key)

        if not authorized:
            return JSONResponse(
                content={"detail": "Unauthorized: Invalid or missing API Secret Key"},
                status_code=401,
                headers={"Access-Control-Allow-Origin": "*"},
            )

    return await call_next(request)

from pydantic import BaseModel
from token_manager import load_token, save_token, verify_token_health, get_token_details

# Include modular routers
app.include_router(config_router)
app.include_router(home_router)
app.include_router(play_router)
app.include_router(category_router)
app.include_router(auth_router)

@app.get("/ott", response_class=HTMLResponse)
async def watch_ott_app(request: Request):
    """
    Serves the premium OTT streaming web player application.
    """
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ott_index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    
    return HTMLResponse(content="<h1>ott_index.html not found!</h1>", status_code=404)

class TokenUpdateRequest(BaseModel):
    token: str

@app.get("/api/proxy/token/status")
async def get_token_status(request: Request):
    """
    Returns the active cached token and verifies its health.
    """
    token = load_token()
    details = await get_token_details(token, request.app.state.http_client)
    return {
        "status": "success",
        "token": token,
        "is_healthy": details.get("is_healthy", False),
        "is_vip": details.get("is_vip", False),
        "payment_status": details.get("payment_status", "free"),
        "plan_name": details.get("plan_name", "Free"),
        "token_preview": token[:15] + "..." if token else "none"
    }

@app.post("/api/proxy/token/update")
async def update_token(request: Request, body: TokenUpdateRequest):
    """
    Updates the cached token in memory and session file, then verifies it.
    """
    new_token = body.token.strip()
    if not new_token:
        return {"status": "error", "message": "Token cannot be empty."}
        
    save_token(new_token)
    details = await get_token_details(new_token, request.app.state.http_client)
    is_healthy = details.get("is_healthy", False)
    
    return {
        "status": "success",
        "is_healthy": is_healthy,
        "is_vip": details.get("is_vip", False),
        "payment_status": details.get("payment_status", "free"),
        "plan_name": details.get("plan_name", "Free"),
        "message": "Token successfully updated and verified." if is_healthy else "Token updated but health verification failed."
    }

# Root endpoint -> 404 Not Found (Sembunyikan eksistensi API dari publik)
@app.get("/")
async def root_index():
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Not Found")

# Secret dashboard endpoint
secret_dashboard_route = os.getenv("DASHBOARD_SECRET_PATH", "/admin/dashboard").strip()
@app.get(secret_dashboard_route, response_class=HTMLResponse)
async def secret_dashboard(request: Request):
    html_content = """<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Viu API Gateway Proxy & Test Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #090a0f;
            --bg-card: rgba(20, 22, 33, 0.75);
            --accent-yellow: #f8c102;
            --accent-yellow-glow: rgba(248, 193, 2, 0.15);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent-blue: #2563eb;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --border-color: rgba(255, 255, 255, 0.06);
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            min-height: 100vh;
            padding: 2.5rem;
            background-image: 
                radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.1) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(248, 193, 2, 0.08) 0px, transparent 50%);
            background-attachment: fixed;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }
        header {
            text-align: center;
            margin-bottom: 1rem;
        }
        header h1 {
            font-size: 2.8rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #ffffff 30%, var(--accent-yellow) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        header p {
            color: var(--text-muted);
            font-size: 1.15rem;
            font-weight: 400;
        }
        .dashboard-layout {
            display: grid;
            grid-template-columns: 450px 1fr;
            gap: 2rem;
            align-items: start;
        }
        @media (max-width: 1024px) {
            .dashboard-layout {
                grid-template-columns: 1fr;
            }
        }
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            backdrop-filter: blur(16px);
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
        }
        .card h2 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-main);
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .card h2::before {
            content: '';
            display: inline-block;
            width: 4px;
            height: 20px;
            background: var(--accent-yellow);
            border-radius: 4px;
            box-shadow: 0 0 10px var(--accent-yellow);
        }
        .endpoint-list {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            max-height: 700px;
            overflow-y: auto;
            padding-right: 0.5rem;
        }
        .endpoint-list::-webkit-scrollbar {
            width: 6px;
        }
        .endpoint-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }
        .endpoint-item {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 1.2rem;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            position: relative;
            overflow: hidden;
        }
        .endpoint-item:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.08);
            transform: translateX(5px);
        }
        .endpoint-item.active {
            background: rgba(248, 193, 2, 0.06);
            border-color: rgba(248, 193, 2, 0.3);
            box-shadow: inset 0 0 20px rgba(248, 193, 2, 0.02);
        }
        .endpoint-item.active::after {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: var(--accent-yellow);
            box-shadow: 0 0 10px var(--accent-yellow);
        }
        .endpoint-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .endpoint-title {
            font-weight: 600;
            font-size: 1.05rem;
            color: #ffffff;
        }
        .badge {
            font-size: 0.7rem;
            font-weight: 800;
            padding: 0.25rem 0.6rem;
            border-radius: 6px;
            letter-spacing: 0.05em;
            background: var(--accent-blue);
            color: #ffffff;
        }
        .badge.GET { background: rgba(37, 99, 235, 0.15); color: #60a5fa; border: 1px solid rgba(37, 99, 235, 0.3); }
        .badge.POST { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
        .endpoint-path {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--accent-cyan);
            word-break: break-all;
        }
        .endpoint-desc {
            font-size: 0.85rem;
            color: var(--text-muted);
            line-height: 1.4;
        }
        /* Right Side Test Console */
        .console-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        .console-header {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .console-header h3 {
            font-size: 1.6rem;
            font-weight: 700;
            color: #ffffff;
        }
        .console-header p {
            color: var(--text-muted);
            font-size: 0.95rem;
        }
        .input-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .input-group label {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .url-bar-container {
            display: flex;
            gap: 0.75rem;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 0.5rem;
            align-items: center;
        }
        .url-method {
            padding: 0.4rem 0.8rem;
            background: rgba(248, 193, 2, 0.1);
            color: var(--accent-yellow);
            border: 1px solid rgba(248, 193, 2, 0.2);
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.85rem;
        }
        .url-input {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: #ffffff;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            width: 100%;
        }
        .btn-execute {
            background: var(--accent-yellow);
            color: #000000;
            border: none;
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 4px 14px rgba(248, 193, 2, 0.3);
        }
        .btn-execute:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(248, 193, 2, 0.5);
            background: #ffffff;
        }
        .btn-execute:active {
            transform: translateY(0);
        }
        .btn-execute:disabled {
            background: #4b5563;
            color: #9ca3af;
            box-shadow: none;
            cursor: not-allowed;
        }
        /* Results Section */
        .results-card {
            display: none;
            flex-direction: column;
            gap: 1.25rem;
            animation: fadeIn 0.4s ease-out forwards;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .results-meta {
            display: flex;
            gap: 1.5rem;
            flex-wrap: wrap;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 1rem;
            border-radius: 12px;
        }
        .meta-item {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .meta-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
        }
        .meta-value {
            font-size: 1.1rem;
            font-weight: 700;
        }
        .meta-value.status-success { color: var(--accent-green); }
        .meta-value.status-error { color: var(--accent-red); }
        .response-body-container {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            position: relative;
        }
        .response-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .response-header h4 {
            font-size: 1rem;
            font-weight: 600;
        }
        .btn-copy {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-main);
            border: 1px solid var(--border-color);
            padding: 0.35rem 0.8rem;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-copy:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .json-viewer-wrapper {
            max-height: 550px;
            overflow-y: auto;
            border-radius: 12px;
            background: #06070a;
            border: 1px solid var(--border-color);
        }
        pre {
            padding: 1.5rem;
            margin: 0;
            overflow-x: auto;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        /* JSON Syntax Highlighting */
        .string { color: #a5d6ff; }
        .number { color: #ff9b72; }
        .boolean { color: #ff7b72; }
        .null { color: #79c0ff; }
        .key { color: #7ee787; font-weight: 600; }
        
        .loading-spinner {
            display: none;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(0,0,0,0.1);
            border-top: 3px solid #000000;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .welcome-screen {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 400px;
            text-align: center;
            color: var(--text-muted);
            gap: 1rem;
        }
        .welcome-screen svg {
            width: 64px;
            height: 64px;
            stroke: var(--accent-yellow);
            opacity: 0.6;
        }
        footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px solid var(--border-color);
        }
        footer a {
            color: var(--accent-yellow);
            text-decoration: none;
            font-weight: 600;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Viu API Gateway Proxy</h1>
            <p>Modular, Asynchronous & Real-Time Reverse Proxy Interactive Test Console</p>
        </header>

        <div class="dashboard-layout">
            <!-- Left Side: Endpoint Directory -->
            <div class="card" style="height: 100%;">
                <!-- Tambah Akun (Login Form) -->
                <div style="margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                    <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--accent-yellow); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-block; width: 8px; height: 8px; background: var(--accent-yellow); border-radius: 50%; box-shadow: 0 0 8px var(--accent-yellow);"></span>
                        Tambah Akun Viu
                    </h3>
                    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div class="input-group">
                            <label style="font-size: 0.75rem; color: var(--text-muted);">Nomor Telepon (Format: 628xxx)</label>
                            <input type="text" id="login-phone" style="width: 100%; height: 40px; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-color); border-radius: 8px; color: #ffffff; padding: 0.4rem 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; outline: none; border-color: rgba(248, 193, 2, 0.15);" placeholder="Contoh: 628123456789">
                        </div>
                        <div class="input-group">
                            <label style="font-size: 0.75rem; color: var(--text-muted);">Password</label>
                            <input type="password" id="login-password" style="width: 100%; height: 40px; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-color); border-radius: 8px; color: #ffffff; padding: 0.4rem 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; outline: none; border-color: rgba(248, 193, 2, 0.15);" placeholder="••••••••">
                        </div>
                        <button class="btn-execute" id="btn-login-submit" onclick="loginViuAccount()" style="padding: 0.6rem 0.8rem; font-size: 0.8rem; background: var(--accent-yellow); box-shadow: 0 4px 10px rgba(248, 193, 2, 0.2); color: #000000; border-radius: 8px; cursor: pointer; border: none; font-weight: 700; transition: all 0.3s ease;">
                            Login & Simpan ke Supabase
                        </button>
                    </div>
                </div>

                <!-- Dynamic Session Recovery Widget -->
                <div style="margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid var(--border-color);">
                    <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--accent-cyan); margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem;">
                        <span style="display: inline-block; width: 8px; height: 8px; background: var(--accent-cyan); border-radius: 50%; box-shadow: 0 0 8px var(--accent-cyan);"></span>
                        Dynamic Session Recovery
                    </h3>
                    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
                        <div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.01); padding: 0.5rem 0.75rem; border-radius: 8px; border: 1px solid rgba(255,255,255,0.04);">
                            <span style="font-size: 0.8rem; color: var(--text-muted);">Session Health:</span>
                            <span id="token-health-badge" class="badge" style="background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid var(--border-color); font-size: 0.65rem;">CHECKING...</span>
                        </div>
                        <div class="input-group">
                            <label style="font-size: 0.75rem; color: var(--text-muted);">Pilih Akun (Supabase Sessions)</label>
                            <select id="account-selector" style="width: 100%; height: 40px; background: rgba(0, 0, 0, 0.3); border: 1px solid var(--border-color); border-radius: 8px; color: #ffffff; padding: 0.4rem 0.5rem; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; outline: none; border-color: rgba(6, 182, 212, 0.15);">
                                <option value="">Loading accounts...</option>
                            </select>
                        </div>
                        <div style="display: flex; gap: 0.5rem;">
                            <button class="btn-execute" id="btn-save-token" onclick="activateSelectedAccount()" style="flex: 1; padding: 0.4rem 0.8rem; font-size: 0.8rem; background: var(--accent-cyan); box-shadow: 0 4px 10px rgba(6, 182, 212, 0.2); color: #000000; border-radius: 8px; cursor: pointer; border: none; font-weight: 700; transition: all 0.3s ease;">
                                Aktifkan Akun
                            </button>
                            <button class="btn-copy" onclick="loadSupabaseAccounts()" style="padding: 0.4rem 0.8rem; font-size: 0.8rem; border-radius: 8px; border: 1px solid var(--border-color); background: rgba(255,255,255,0.05); color: #fff; cursor: pointer; transition: all 0.2s;" title="Refresh daftar akun">
                                ↻
                            </button>
                        </div>
                    </div>
                </div>

                <h2>Daftar API Endpoint</h2>
                <div class="endpoint-list" id="endpoint-list-container">
                    <!-- Dynamic Endpoint Cards -->
                </div>
            </div>

            <!-- Right Side: Test Console & Response Panel -->
            <div class="card" style="min-height: 600px;">
                <div id="welcome-panel" class="welcome-screen">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
                    </svg>
                    <h3>Konsol Pengujian Interaktif</h3>
                    <p>Silakan pilih salah satu endpoint di sebelah kiri untuk mulai melakukan test request secara real-time.</p>
                </div>

                <div id="console-panel" class="console-container" style="display: none;">
                    <div class="console-header">
                        <h3 id="endpoint-display-name">Endpoint Name</h3>
                        <p id="endpoint-display-desc">Description</p>
                    </div>

                    <div class="input-group">
                        <label>Request Gateway URL</label>
                        <div class="url-bar-container">
                            <span class="url-method">GET</span>
                            <span style="color: var(--text-muted); font-family: monospace;">http://127.0.0.1:6105</span>
                            <input type="text" class="url-input" id="endpoint-url-input" value="/api/config">
                            <button class="btn-execute" id="btn-run-test" onclick="executeCurrentTest()">
                                <div class="loading-spinner" id="test-spinner"></div>
                                <span id="btn-text">Kirim Request</span>
                            </button>
                        </div>
                    </div>

                    <!-- Live Test Results Panel -->
                    <div class="results-card" id="results-panel">
                        <div class="results-meta">
                            <div class="meta-item">
                                <span class="meta-label">Status HTTP</span>
                                <span class="meta-value" id="res-status">-</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Response Time</span>
                                <span class="meta-value" style="color: var(--accent-yellow);" id="res-time">-</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Ukuran Data</span>
                                <span class="meta-value" style="color: var(--accent-cyan);" id="res-size">-</span>
                            </div>
                            <div class="meta-item">
                                <span class="meta-label">Content Type</span>
                                <span class="meta-value" id="res-type">-</span>
                            </div>
                        </div>

                        <div class="response-body-container">
                            <!-- Download Bypass Container (Loopholes) -->
                            <div id="download-bypass-container" style="display: none; background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1rem; align-items: center; justify-content: space-between; gap: 1rem; box-shadow: 0 4px 20px rgba(6, 182, 212, 0.05); width: 100%;">
                                <div style="flex: 1;">
                                    <h5 style="color: var(--accent-cyan); font-size: 0.95rem; font-weight: 700; margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.5rem;">
                                        <span style="display: inline-block; width: 6px; height: 6px; background: var(--accent-cyan); border-radius: 50%; box-shadow: 0 0 6px var(--accent-cyan);"></span>
                                        🔓 Bypass Loophole Detected!
                                    </h5>
                                    <p style="color: var(--text-muted); font-size: 0.8rem; margin: 0; line-height: 1.4;">Tautan langsung berkas video berdurasi penuh (100% Full Duration) berhasil diekstraksi dari CDN Viu.</p>
                                </div>
                                <a id="btn-download-bypass" href="#" target="_blank" style="background: var(--accent-cyan); color: #000000; text-decoration: none; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 700; border-radius: 8px; box-shadow: 0 4px 10px rgba(6, 182, 212, 0.3); transition: all 0.3s ease; text-align: center; white-space: nowrap;">Unduh Full Video (.ts)</a>
                            </div>

                            <div class="response-header">
                                <h4>Response Body (Formatted JSON)</h4>
                                <button class="btn-copy" onclick="copyResponseToClipboard()">Salin Data</button>
                            </div>
                            <div class="json-viewer-wrapper">
                                <pre id="json-pre-code">Code</pre>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>Dikembangkan secara profesional dengan FastAPI &bull; <a href="/docs" target="_blank">Swagger API Docs</a> &bull; <a href="/redoc" target="_blank">Redoc</a></p>
        </footer>
    </div>

    <script>
        const endpoints = [
            {
                id: "config",
                name: "Server Configuration",
                method: "GET",
                path: "/api/config",
                defaultParams: "platform_flag_label=web&area_id=1000",
                description: "Mengambil konfigurasi server, carrier telekomunikasi, deteksi IP klien, dan kode negara secara real-time."
            },
            {
                id: "recommendations",
                name: "Audience Recommendations",
                method: "GET",
                path: "/api/audienceTargeting/recommendations",
                defaultParams: "platform_flag_label=web&area_id=1000&language_flag_id=8&pageType=home&pageId=0",
                description: "Mengambil carousel list halaman utama, kategori drama trending, dan detail produk film/drama terpopuler langsung dari Viu Gateway."
            },
            {
                id: "user_info",
                name: "User Session Profile",
                method: "GET",
                path: "/api/user/info",
                defaultParams: "platform_flag_label=web&area_id=1000&language_flag_id=8",
                description: "Mengambil rincian profil pengguna aktif, perizinan kualitas resolusi, dan pengaturan bahasa sesi."
            },
            {
                id: "subscription",
                name: "Subscription Status",
                method: "GET",
                path: "/api/subscription/status",
                defaultParams: "platform_flag_label=web&area_id=1000&language_flag_id=8",
                description: "Menguji status keanggotaan pengguna, data pelacakan analitik, dan detail paket langganan aktif."
            },
            {
                id: "category_korea",
                name: "Category: Drama Korea (ID 549)",
                method: "GET",
                path: "/api/mobile",
                defaultParams: "r=/category/series&category_id=549&length=44&offset=0",
                description: "Mengambil daftar drama terlengkap dalam kategori spesifik secara real-time (ID 549 = Drama Korea)."
            },
            {
                id: "category_dub_indo",
                name: "Category: Dub Indo (ID 553)",
                method: "GET",
                path: "/api/mobile",
                defaultParams: "r=/category/series&category_id=553&length=44&offset=0",
                description: "Mengambil daftar drama khusus yang di-Dubbing ke Bahasa Indonesia secara real-time."
            },
            {
                id: "vod_detail",
                name: "VOD Detail & Subtitle",
                method: "GET",
                path: "/api/mobile",
                defaultParams: "r=/vod/detail&product_id=3095829&os_flag_id=1",
                description: "Mengambil rincian video, sinopsis, daftar aktor, serta tautan Subtitle Lengkap secara real-time."
            },
            {
                id: "episode_list",
                name: "Series Episode List",
                method: "GET",
                path: "/api/mobile",
                defaultParams: "r=/vod/product-list&series_id=104436&size=50&sort=ASC",
                description: "Mengambil daftar seluruh episode lengkap untuk series/drama tertentu (ID 104436 = Dazzling)."
            },
            {
                id: "search_drama",
                name: "Drama Search",
                method: "GET",
                path: "/api/drama-api/search",
                defaultParams: "q=Blossom+Through+the+Cloud&page=1&limit=5",
                description: "Mencari drama/film berdasarkan keyword. Mengembalikan daftar hasil beserta product_id yang sudah di-resolve (siap dipakai sebagai URL /viu/detail/:id)."
            },
            {
                id: "playback",
                name: "Playback Distribution",
                method: "GET",
                path: "/api/playback/distribute",
                defaultParams: "platform_flag_label=web&area_id=1000&ccs_product_id=1166303805",
                description: "Mengambil link streaming HLS (.m3u8) aktif dengan otentikasi fallback otomatis secara real-time."
            },
            {
                id: "drm_key",
                name: "DRM Key Resolution",
                method: "GET",
                path: "/api/appsdrm/getkey",
                defaultParams: "sn=2931&cid=1166303805",
                description: "Menghubungi server lisensi DRM Viu untuk mendapatkan sertifikat dekripsi streaming video."
            },
            {
                id: "category_list",
                name: "WeTV Style Mapped Category List",
                method: "GET",
                path: "/api/category",
                defaultParams: "language_flag_id=8",
                description: "Mengambil daftar 14 kategori utama dalam format kustom WeTV secara real-time. Mendukung penerjemahan bahasa otomatis berdasarkan language_flag_id (8 = Indo, 3 = English)."
            }
        ];

        let selectedEndpoint = null;
        let lastResponseText = "";

        // Build list cards
        const listContainer = document.getElementById("endpoint-list-container");
        endpoints.forEach(ep => {
            const card = document.createElement("div");
            card.className = "endpoint-item";
            card.id = `ep-card-${ep.id}`;
            card.onclick = () => selectEndpoint(ep);
            card.innerHTML = `
                <div class="endpoint-header">
                    <span class="endpoint-title">${ep.name}</span>
                    <span class="badge ${ep.method}">${ep.method}</span>
                </div>
                <div class="endpoint-path">${ep.path}</div>
                <div class="endpoint-desc">${ep.description}</div>
            `;
            listContainer.appendChild(card);
        });

        function selectEndpoint(ep) {
            // Update active states
            endpoints.forEach(item => {
                const el = document.getElementById(`ep-card-${item.id}`);
                if (el) el.classList.remove("active");
            });
            document.getElementById(`ep-card-${ep.id}`).classList.add("active");

            // Show console panels
            document.getElementById("welcome-panel").style.display = "none";
            document.getElementById("console-panel").style.display = "flex";
            document.getElementById("results-panel").style.display = "none";

            selectedEndpoint = ep;

            // Populate inputs
            document.getElementById("endpoint-display-name").innerText = ep.name;
            document.getElementById("endpoint-display-desc").innerText = ep.description;
            
            const fullPath = ep.defaultParams ? `${ep.path}?${ep.defaultParams}` : ep.path;
            document.getElementById("endpoint-url-input").value = fullPath;
        }

        async function executeCurrentTest() {
            if (!selectedEndpoint) return;

            const urlInputVal = document.getElementById("endpoint-url-input").value;
            const spinner = document.getElementById("test-spinner");
            const btnText = document.getElementById("btn-text");
            const runBtn = document.getElementById("btn-run-test");
            const resultsPanel = document.getElementById("results-panel");

            // UI loading state
            spinner.style.display = "inline-block";
            btnText.innerText = "Mengirim...";
            runBtn.disabled = true;
            resultsPanel.style.display = "none";
            document.getElementById("download-bypass-container").style.display = "none";

            const startTime = performance.now();

            try {
                const response = await fetch(urlInputVal);
                const endTime = performance.now();
                const latency = Math.round(endTime - startTime);

                const statusVal = document.getElementById("res-status");
                statusVal.innerText = `${response.status} ${response.statusText || ''}`;
                if (response.ok) {
                    statusVal.className = "meta-value status-success";
                } else {
                    statusVal.className = "meta-value status-error";
                }

                document.getElementById("res-time").innerText = `${latency} ms`;
                
                const contentType = response.headers.get("content-type") || "unknown";
                document.getElementById("res-type").innerText = contentType.split(";")[0];

                let data;
                let sizeBytes = 0;

                if (contentType.includes("application/json")) {
                    data = await response.json();
                    lastResponseText = JSON.stringify(data, null, 2);
                    sizeBytes = new Blob([lastResponseText]).size;
                    
                    document.getElementById("json-pre-code").innerHTML = syntaxHighlight(data);

                    // Show download bypass banner if full progressive URL is found
                    const bypassContainer = document.getElementById("download-bypass-container");
                    const bypassBtn = document.getElementById("btn-download-bypass");
                    if (data && data.data && data.data.full_progressive_download_url) {
                        bypassBtn.href = data.data.full_progressive_download_url;
                        bypassContainer.style.display = "flex";
                    } else {
                        bypassContainer.style.display = "none";
                    }
                } else {
                    // For binary data e.g. DRM key
                    const arrayBuffer = await response.arrayBuffer();
                    sizeBytes = arrayBuffer.byteLength;
                    lastResponseText = `[Payload Binary Data: ${sizeBytes} bytes]`;
                    
                    // Show beautiful binary/hex info
                    let hexText = `/* DATA STREAM BINARY (${sizeBytes} bytes) */\\n\\n`;
                    const view = new Uint8Array(arrayBuffer.slice(0, 128));
                    hexText += "Hex Dump (First 128 Bytes):\\n";
                    let hexLine = "";
                    let asciiLine = "";
                    for(let i=0; i<view.length; i++) {
                        hexLine += view[i].toString(16).padStart(2, '0').toUpperCase() + " ";
                        asciiLine += (view[i] >= 32 && view[i] <= 126) ? String.fromCharCode(view[i]) : ".";
                        if((i + 1) % 16 === 0 || i === view.length - 1) {
                            hexText += hexLine.padEnd(48, ' ') + " | " + asciiLine + "\\n";
                            hexLine = "";
                            asciiLine = "";
                        }
                    }
                    if (sizeBytes > 128) {
                        hexText += `\\n... dan ${sizeBytes - 128} bytes data biner lainnya.`;
                    }
                    document.getElementById("json-pre-code").innerHTML = `<span class="string">${hexText}</span>`;
                }

                // Format size
                const sizeKB = (sizeBytes / 1024).toFixed(2);
                document.getElementById("res-size").innerText = `${sizeKB} KB`;

                // Show panel
                resultsPanel.style.display = "flex";

            } catch (err) {
                const endTime = performance.now();
                const latency = Math.round(endTime - startTime);

                document.getElementById("res-status").innerText = "Network Error";
                document.getElementById("res-status").className = "meta-value status-error";
                document.getElementById("res-time").innerText = `${latency} ms`;
                document.getElementById("res-size").innerText = "0 KB";
                document.getElementById("res-type").innerText = "none";

                document.getElementById("json-pre-code").innerHTML = `<span class="null">Error: Gagal melakukan request ke proxy local server.\\nDetail: ${err.message}</span>`;
                resultsPanel.style.display = "flex";
            } finally {
                spinner.style.display = "none";
                btnText.innerText = "Kirim Request";
                runBtn.disabled = false;
            }
        }

        function copyResponseToClipboard() {
            if (!lastResponseText) return;
            navigator.clipboard.writeText(lastResponseText).then(() => {
                const copyBtn = document.querySelector(".btn-copy");
                const originalText = copyBtn.innerText;
                copyBtn.innerText = "Tersalin!";
                copyBtn.style.background = "var(--accent-green)";
                copyBtn.style.color = "#000000";
                setTimeout(() => {
                    copyBtn.innerText = originalText;
                    copyBtn.style.background = "rgba(255, 255, 255, 0.05)";
                    copyBtn.style.color = "var(--text-main)";
                }, 2000);
            });
        }

        // Format JSON utility function
        function syntaxHighlight(json) {
            if (typeof json !== 'string') {
                 json = JSON.stringify(json, undefined, 2);
            }
            json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\\s*:)?|\\b(true|false|null)\\b|-?\\d+(?:\\.\\d*)?(?:[eE][+-]?\\d+)?)/g, function (match) {
                let cls = 'number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'key';
                    } else {
                        cls = 'string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'boolean';
                } else if (/null/.test(match)) {
                    cls = 'null';
                }
                return '<span class="' + cls + '">' + match + '</span>';
            });
        }
        // Form Login Handler
        async function loginViuAccount() {
            const phone = document.getElementById("login-phone").value.trim();
            const password = document.getElementById("login-password").value.trim();
            const btn = document.getElementById("btn-login-submit");

            if (!phone || !password) {
                alert("Nomor telepon dan password wajib diisi!");
                return;
            }

            btn.disabled = true;
            btn.innerText = "Memproses Login...";

            try {
                const response = await fetch("/api/auth/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ phone, password, provider: "phone" })
                });
                const data = await response.json();

                if (response.ok && data.status === "success") {
                    alert(`Login Berhasil!\nAkun: ${data.nickname || data.username}\nPlan: ${data.plan_name}\nStatus: ${data.is_vip ? 'VIP' : 'FREE'}`);
                    document.getElementById("login-phone").value = "";
                    document.getElementById("login-password").value = "";
                    await loadSupabaseAccounts(); // refresh list
                    checkTokenStatus(); // resync dropdown selection
                } else {
                    alert(`Login Gagal: ${data.detail || data.message || 'Periksa kembali kredensial Anda.'}`);
                }
            } catch (err) {
                alert("Gagal menghubungi server: " + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = "Login & Simpan ke Supabase";
            }
        }

        // Token Health Check & Auto Recovery System JS
        async function loadSupabaseAccounts() {
            const selector = document.getElementById("account-selector");
            const savedToken = localStorage.getItem("selectedViuToken");
            const currentToken = selector.value || savedToken;

            selector.innerHTML = '<option value="">Loading accounts...</option>';
            try {
                const response = await fetch("/api/supabase/sessions");
                const data = await response.json();
                selector.innerHTML = "";
                if (data.status === "success" && data.sessions.length > 0) {
                    data.sessions.forEach(session => {
                        const isVip = session.is_vip ? "⭐ VIP" : "FREE";
                        const plan = session.plan_name ? `(${session.plan_name})` : "";
                        const option = document.createElement("option");
                        option.value = session.token;
                        option.text = `${session.username} - ${isVip} ${plan}`;
                        selector.appendChild(option);
                    });
                    if (currentToken) {
                        selector.value = currentToken;
                    }
                } else {
                    selector.innerHTML = '<option value="">Belum ada akun di Supabase</option>';
                }
            } catch (err) {
                selector.innerHTML = '<option value="">Eror memuat akun</option>';
            }
        }

        async function activateSelectedAccount() {
            const badge = document.getElementById("token-health-badge");
            const selector = document.getElementById("account-selector");
            const saveBtn = document.getElementById("btn-save-token");
            
            const tokenVal = selector.value;
            if (!tokenVal) {
                alert("Pilih akun terlebih dahulu!");
                return;
            }
            
            saveBtn.disabled = true;
            saveBtn.innerText = "Mengaktifkan...";
            badge.innerText = "VERIFIKASI...";
            
            try {
                const response = await fetch("/api/proxy/token/update", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ token: tokenVal })
                });
                const data = await response.json();
                
                if (data.is_healthy) {
                    if (data.is_vip) {
                        badge.innerText = `AKTIF & VALID (VIP - ${data.plan_name.toUpperCase()})`;
                        badge.style.background = "rgba(248, 193, 2, 0.15)";
                        badge.style.color = "var(--accent-gold)";
                        badge.style.border = "1px solid rgba(248, 193, 2, 0.3)";
                        alert(`Akun berhasil diaktifkan!\nPlan: ${data.plan_name}\nVIP Status: VIP`);
                    } else {
                        badge.innerText = "AKTIF & VALID (FREE USER - LIMITED)";
                        badge.style.background = "rgba(239, 68, 68, 0.15)";
                        badge.style.color = "#f87171";
                        badge.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                        alert(`Akun berhasil diaktifkan!\nPlan: ${data.plan_name}\nVIP Status: FREE`);
                    }
                } else {
                    badge.innerText = "INVALID/EXPIRED";
                    badge.style.background = "rgba(239, 68, 68, 0.15)";
                    badge.style.color = "#f87171";
                    badge.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                    alert("Akun berhasil dipilih, tetapi hasil verifikasi EXPIRED/INVALID.");
                }
            } catch (err) {
                badge.innerText = "EROR KONEKSI";
                alert("Gagal mengaktifkan akun: " + err.message);
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerText = "Aktifkan Akun";
            }
        }

        async function checkTokenStatus() {
            const badge = document.getElementById("token-health-badge");
            
            badge.innerText = "MENGECEK...";
            badge.className = "badge";
            badge.style.background = "rgba(255, 255, 255, 0.05)";
            badge.style.color = "var(--text-muted)";
            badge.style.border = "1px solid var(--border-color)";

            try {
                const response = await fetch("/api/proxy/token/status");
                const data = await response.json();
                
                // Select the option if it exists in the dropdown
                const selector = document.getElementById("account-selector");
                if (data.token) {
                    for (let i = 0; i < selector.options.length; i++) {
                        if (selector.options[i].value === data.token) {
                            selector.selectedIndex = i;
                            localStorage.setItem("selectedViuToken", data.token);
                            break;
                        }
                    }
                }
                
                if (data.is_healthy) {
                    if (data.is_vip) {
                        badge.innerText = `AKTIF & VALID (VIP - ${data.plan_name.toUpperCase()})`;
                        badge.style.background = "rgba(248, 193, 2, 0.15)";
                        badge.style.color = "var(--accent-gold)";
                        badge.style.border = "1px solid rgba(248, 193, 2, 0.3)";
                    } else {
                        badge.innerText = "AKTIF & VALID (FREE USER - LIMITED)";
                        badge.style.background = "rgba(239, 68, 68, 0.15)";
                        badge.style.color = "#f87171";
                        badge.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                    }
                } else {
                    badge.innerText = "EXPIRED / INVALID";
                    badge.style.background = "rgba(239, 68, 68, 0.15)";
                    badge.style.color = "#f87171";
                    badge.style.border = "1px solid rgba(239, 68, 68, 0.3)";
                }
            } catch (err) {
                badge.innerText = "EROR KONEKSI";
                badge.style.background = "rgba(239, 68, 68, 0.15)";
                badge.style.color = "#f87171";
            }
        }

        // Initialize status check on DOM load
        window.addEventListener("DOMContentLoaded", async () => {
            document.getElementById("account-selector").addEventListener("change", (e) => {
                localStorage.setItem("selectedViuToken", e.target.value);
            });
            await loadSupabaseAccounts();
            checkTokenStatus();
        });
    </script>
</body>
</html>"""
    return html_content

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 6105))
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "t")
    uvicorn.run("main:app", host=host, port=port, reload=reload)
