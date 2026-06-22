"""Launch the Privacy Firewall API server.

This script starts the FastAPI backend server.
The frontend is served separately by the Next.js app in pii-web-next.

Usage:
    python run_playground.py
    
Then access the API at: http://localhost:8080/docs
Frontend (separate): http://localhost:3000 (run from pii-web-next)
"""

from privacy_firewall.web import create_app
from pathlib import Path
import os


def main() -> None:
    """Start the Privacy Firewall API server."""
    # Optional: load environment variables from .env
    try:
        from dotenv import load_dotenv

        env_file = Path(__file__).with_name(".env")
        if env_file.exists():
            load_dotenv(env_file)
    except Exception:
        # dotenv is optional
        pass

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "uvicorn not installed. Run: pip install -e .[web]"
        ) from exc

    print("=" * 70)
    print("🚀 Privacy Firewall - API Server")
    print("=" * 70)
    print()
    print("Starting FastAPI server...")
    print("  API Documentation: http://localhost:8080/docs")
    print("  Health Check:      http://localhost:8080/health")
    print("  Runtime Options:   http://localhost:8080/api/runtime-options")
    print()
    print("Frontend: Run separately from pii-web-next folder")
    print("  $ cd ../pii-web-next")
    print("  $ npm run dev")
    print()
    print("=" * 70)
    print()

    app = create_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
