#!/usr/bin/env python3
"""
FreeReels API Proxy Server - Production Entry Point
Run: python run_proxy.py
Access: http://localhost:8000
"""

import sys
import os

# Add production root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.proxy import app
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "6106"))

    print("="*70)
    print("FreeReels API Proxy Server v1.4.0")
    print("="*70)
    print("Starting server...")
    print(f"Playground: http://localhost:{port}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Custom tabs: http://localhost:{port}/api/tabs/complete")
    print("\nPress CTRL+C to stop")
    print("="*70)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
