"""Server runner for iQIYI API service."""
import os
import sys
from pathlib import Path

# Add project root to Python path so production.main can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from dotenv import load_dotenv


def main():
    """Run iQIYI API server."""
    # Load environment variables
    load_dotenv(dotenv_path=project_root / ".env")
    
    # Get configuration
    host = os.getenv("HOST", os.getenv("SERVER_HOST", "127.0.0.1"))
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", 7407)))
    
    print(f"Starting iQIYI API Server...")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Documentation: http://localhost:{port}/docs")
    print(f"ReDoc: http://localhost:{port}/redoc")
    print()
    
    reload = os.getenv("RELOAD", "false").lower() in ("true", "1", "t")
    try:
        uvicorn.run(
            "production.main:app",
            host=host,
            port=port,
            reload=reload,
            reload_dirs=[str(project_root)] if reload else None,
            log_level="info",
        )
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {port} is already in use")
            print(f"Please choose a different port or stop the process using port {port}")
            sys.exit(1)
        raise


if __name__ == "__main__":
    main()
