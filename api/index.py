import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend_dir = root / "backend"

sys.path.insert(0, str(backend_dir))
os.environ.setdefault("DOCS_DIR", str(backend_dir / "documents"))

from main import app
