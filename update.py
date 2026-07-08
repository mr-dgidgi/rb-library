
#!/usr/bin/env python3
"""Update library.json by scanning PDFs and interactively adding missing entries.

Usage:
	python update.py            # CLI mode (interactive)

The script looks for `library.json` in the same folder and scans the current
directory for PDF files. For each PDF not already listed in `file_list`, it
asks the user for a name, language and category, then appends the entry.
"""

from pathlib import Path
import json
import argparse
import shutil
import sys

# Require Python 3.6+ for f-strings and type hints
if sys.version_info < (3, 6):
	print("This script requires Python 3.6 or newer. Run it with 'python3'.")
	sys.exit(1)


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


def find_pdfs(directory: Path):
	return sorted([p.name for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])


def is_present(lib, filename: str):
	for v in lib.get("file_list", {}).values():
		if v.get("id") == filename:
			return True
	return False


def next_key(lib):
	keys = [int(k) for k in lib.get("file_list", {}).keys() if k.isdigit()]
	return str(max(keys) + 1) if keys else "1"


def prompt_with_default(prompt, default):
	if default:
		ans = input(f"{prompt} [{default}]: ").strip()
		return ans if ans else default
	else:
		return input(f"{prompt}: ").strip()


def choose_from_known(prompt_label: str, options: list, lib_key: str, lib: dict):
	"""Ask user to choose from known options or enter a new one.

	If a new value is entered, append it to lib[lib_key].
	"""
	if options:
		print(f"Known {prompt_label}s:")
		for i, o in enumerate(options, 1):
			print(f"{i}) {o}")
		print("n) Enter a new value")
		choice = input(f"Select number or 'n' to enter new {prompt_label}: ").strip()
		if choice.isdigit() and 1 <= int(choice) <= len(options):
			return options[int(choice) - 1]
		else:
			val = input(f"Enter new {prompt_label}: ").strip()
			if val:
				lib.setdefault(lib_key, []).append(val)
			return val
	else:
		val = input(f"Enter {prompt_label}: ").strip()
		if val:
			lib.setdefault(lib_key, []).append(val)
		return val


def cli_mode(root: Path, lib_path: Path):
	lib = ensure_default_lists(load_library(lib_path))
	pdfs = find_pdfs(root)
	changed = False

	cats = lib.get("category", []) or []
	langs = lib.get("language", []) or []
	types = lib.get("type", []) or []

	for pdf in pdfs:
		if is_present(lib, pdf):
			continue
		print(f"\nFound new PDF: {pdf}")
		default_name = Path(pdf).stem.replace("_", " ")
		name = prompt_with_default("Name", default_name)

		# Validate language and category against known lists (allow adding new)
		language = choose_from_known("language", langs, "language", lib)
		while not language:
			print("Language cannot be empty.")
			language = choose_from_known("language", langs, "language", lib)

		category = choose_from_known("category", cats, "category", lib)
		while not category:
			print("Category cannot be empty.")
			category = choose_from_known("category", cats, "category", lib)

		type_value = choose_from_known("type", types, "type", lib)
		while not type_value:
			print("Type cannot be empty.")
			type_value = choose_from_known("type", types, "type", lib)

		key = next_key(lib)
		lib.setdefault("file_list", {})[key] = {
			"id": pdf,
			"name": name,
			"category": category,
			"language": language,
			"type": type_value,
		}
		print(f"Added entry under key {key}.")
		# Save immediately to avoid data loss if interrupted
		save_library(lib, lib_path)
		print(f"library.json updated (saved after adding key {key}).")
		changed = True

	if changed:
		save_library(lib, lib_path)
		print(f"library.json updated: {lib_path}")
	else:
		print("No new PDFs to add.")


# Web UI removed: we provide an interactive CLI only per user request.


def main():
	parser = argparse.ArgumentParser(description="Update library.json from PDFs (CLI only)")
	parser.add_argument("--dir", default=".", help="Directory to scan for PDFs")
	args = parser.parse_args()

	root = Path(args.dir).resolve()
	lib_path = Path(__file__).resolve().parent / "library.json"

	cli_mode(root, lib_path)


if __name__ == "__main__":
	main()
