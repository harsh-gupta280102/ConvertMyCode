"""
PyConvert Main Entry Point
Launches FastAPI backend server and automatically opens browser interface.
"""
import sys
import os
import time
import argparse
import webbrowser
import threading
import uvicorn

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.config import DEFAULT_HOST, DEFAULT_PORT
from app.server import app

# Ensure stdout supports UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def open_browser(url: str, delay: float = 1.2):
    """Opens browser after server has started"""
    def _open():
        time.sleep(delay)
        print(f"Opening PyConvert Studio at {url}")
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

def main():
    parser = argparse.ArgumentParser(description="PyConvert - JavaScript to TypeScript Project Converter with Gemini AI")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to run server on (default: 8000)")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open web browser")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()
    url = f"http://{args.host}:{args.port}"

    print("=" * 65)
    print("  PyConvert: JavaScript to TypeScript Studio (Powered by Gemini AI)")
    print(f"  Running on: {url}")
    print("=" * 65)

    if not args.no_browser:
        open_browser(url)

    uvicorn.run(
        "app.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
