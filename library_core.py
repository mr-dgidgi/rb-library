"""Shared library scanning/read/write logic used by the CLI script and the admin web backend."""

from pathlib import Path
import json
import shutil


def load_library(path: Path):
	if not path.exists():
		return {"category": [], "language": [], "file_list": {}}
	with path.open("r", encoding="utf-8") as f:
		return json.load(f)


def save_library(data, path: Path):
	# backup
	if path.exists():
		shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
	# maintain a simple count of files in the library
	try:
		data["count"] = len(data.get("file_list", {}))
	except Exception:
		data["count"] = 0
	with path.open("w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=4)


def ensure_default_lists(lib: dict):
	"""Ensure known lists exist with default values used by the CLI."""
	if not lib.get("type"):
		lib["type"] = ["book", "printable"]
	return lib


def find_pdfs(root: Path):
	pdf_dirs = [
		(root / "PDF", False),
		(root / "PDF" / "custom", True),
	]
	files = []
	custom_files = []
	for directory, is_custom in pdf_dirs:
		if not directory.exists():
			continue
		for p in directory.iterdir():
			if p.is_file() and p.suffix.lower() == ".pdf":
				if is_custom:
					custom_files.append(p.name)
				else:
					files.append(p.name)
	return sorted(files), sorted(custom_files)


def is_present(lib, filename: str):
	for v in lib.get("file_list", {}).values():
		if v.get("id") == filename:
			return True
	return False


def next_key(lib):
	keys = [int(k) for k in lib.get("file_list", {}).keys() if k.isdigit()]
	return str(max(keys) + 1) if keys else "1"
