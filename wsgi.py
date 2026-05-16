"""
WSGI entry point для Render / Gunicorn.
Render ищет переменную `server` в этом файле.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.dashboard.app import app

server = app.server  # Flask instance за Dash

if __name__ == "__main__":
    server.run()
