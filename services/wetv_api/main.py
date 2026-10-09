from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hide Swagger / OpenAPI docs if DEBUG is False
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
app = FastAPI(
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
    openapi_url="/openapi.json" if DEBUG else None
)

# CORS configuration
origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [o.strip() for o in origins_str.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bearer Auth middleware — aktif hanya jika API_SECRET_KEY diisi di .env
@app.middleware("http")
async def bearer_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/wetv/"):
        if request.method != "OPTIONS":
            secret_key = os.getenv("API_SECRET_KEY", "").strip()
            if secret_key:
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        content={"detail": "Missing or invalid Authorization header"},
                        status_code=401
                    )
                token = auth_header.split(" ", 1)[1]
                if token != secret_key:
                    return JSONResponse(
                        content={"detail": "Invalid API Secret Key"},
                        status_code=401
                    )
    return await call_next(request)

# Import and include home, search, album, and play routers
from home import router as home_router
from search import router as search_router
from album import router as album_router
from play import router as play_router

app.include_router(home_router)
app.include_router(search_router)
app.include_router(album_router)
app.include_router(play_router)

# Root route -> 404 (Sembunyikan eksistensi server)
@app.get("/")
async def root():
    raise HTTPException(status_code=404, detail="Not Found")

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", 7402))
    # Jalankan server uvicorn pada port 7402
    uvicorn.run("main:app", host=host, port=port, reload=DEBUG)
