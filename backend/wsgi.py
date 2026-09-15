"""Entry point for Apache mod_wsgi (WSGIScriptAlias -> this file, application object)."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from backend.app import app as application  # noqa: E402
