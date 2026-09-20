#!/usr/bin/env python3
"""Update library data by scanning PDFs and interactively adding missing entries.

Usage:
	library-update.py            # CLI mode (interactive)

The script looks for `library.json` in the same folder and
`custom-library.json` under `PDF/custom/`, and scans the `PDF` and
`PDF/custom` subdirectories for PDF files.
For each PDF not already listed in the relevant `file_list`, it asks the user
for a name, language and category, then appends the entry.
"""

from pathlib import Path
import argparse
import sys

# Require Python 3.6+ for f-strings and type hints
if sys.version_info < (3, 6):
	print("This script requires Python 3.6 or newer. Run it with 'python3'.")
	sys.exit(1)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from library_core import (  # noqa: E402
	load_library,
	save_library,
	ensure_default_lists,
	find_pdfs,
	is_present,
	next_key,
)


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


def cli_mode(root: Path, lib_path: Path, custom_lib_path: Path):
	lib = ensure_default_lists(load_library(lib_path))
	custom_lib = ensure_default_lists(load_library(custom_lib_path))
	pdfs, custom_pdfs = find_pdfs(root)
	changed = False

	def process_pdf(pdf: str, target_lib: dict, target_path: Path, label: str):
		nonlocal changed
		if is_present(target_lib, pdf):
			return
		print(f"\nFound new PDF for {label}: {pdf}")
		default_name = Path(pdf).stem.replace("_", " ")
		name = prompt_with_default("Name", default_name)

		cats = target_lib.get("category", []) or []
		langs = target_lib.get("language", []) or []
		types = target_lib.get("type", []) or []
		if not cats and lib.get("category"):
			cats = lib.get("category", []) or []
		if not langs and lib.get("language"):
			langs = lib.get("language", []) or []
		if not types and lib.get("type"):
			types = lib.get("type", []) or []

		# Validate language and category against known lists (allow adding new)
		language = choose_from_known("language", langs, "language", target_lib)
		while not language:
			print("Language cannot be empty.")
			language = choose_from_known("language", langs, "language", target_lib)

		category = choose_from_known("category", cats, "category", target_lib)
		while not category:
			print("Category cannot be empty.")
			category = choose_from_known("category", cats, "category", target_lib)

		type_value = choose_from_known("type", types, "type", target_lib)
		while not type_value:
			print("Type cannot be empty.")
			type_value = choose_from_known("type", types, "type", target_lib)

		key = next_key(target_lib)
		target_lib.setdefault("file_list", {})[key] = {
			"id": pdf,
			"name": name,
			"category": category,
			"language": language,
			"type": type_value,
		}
		print(f"Added entry under key {key}.")
		# Save immediately to avoid data loss if interrupted
		save_library(target_lib, target_path)
		print(f"{target_path.name} updated (saved after adding key {key}).")
		changed = True

	for pdf in pdfs:
		process_pdf(pdf, lib, lib_path, "main library")

	for pdf in custom_pdfs:
		process_pdf(pdf, custom_lib, custom_lib_path, "custom library")

	if changed:
		print(f"library.json updated: {lib_path}")
		print(f"custom-library.json updated: {custom_lib_path}")
	else:
		print("No new PDFs to add.")


# Web UI removed: we provide an interactive CLI only per user request.


def main():
	parser = argparse.ArgumentParser(description="Update library.json from PDFs (CLI only)")
	parser.add_argument("--dir", default=None, help="Root directory to scan for PDFs. Defaults to the script directory.")
	args = parser.parse_args()

	script_dir = Path(__file__).resolve().parent
	root = Path(args.dir).resolve() if args.dir else script_dir
	lib_path = script_dir / "library.json"
	custom_lib_path = script_dir / "PDF" / "custom" / "custom-library.json"

	cli_mode(root, lib_path, custom_lib_path)


if __name__ == "__main__":
	main()
