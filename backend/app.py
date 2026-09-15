"""Flask admin backend for web-based indexation of PDF/custom.

Runs under Apache mod_wsgi with WSGIDaemonProcess user=recuser group=recuser
so writes land with the correct ownership (PDF/custom and custom-library.json
belong to recuser; library.json and PDF/ stay root-owned and read-only here).
Authentication is delegated to PAM and restricted to the system account whose
uid matches RB_LIBRARY_ADMIN_UID (default 1000) - the username is resolved
dynamically, so the app stays agnostic of the actual account name.
"""

import json
import os
import pwd
import re
import sys
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from library_core import (  # noqa: E402
	load_library,
	save_library,
	ensure_default_lists,
	find_pdfs,
	is_present,
	next_key,
)

try:
	import pam
except ImportError:  # pam is only required at runtime on the target host
	pam = None

ROOT_DIR = Path(__file__).resolve().parent.parent
LIBRARY_PATH = ROOT_DIR / "library.json"
CUSTOM_LIBRARY_PATH = ROOT_DIR / "custom-library.json"

ALLOWED_UID = int(os.environ.get("RB_LIBRARY_ADMIN_UID", "1000"))


def _resolve_allowed_username(uid):
	try:
		return pwd.getpwuid(uid).pw_name
	except KeyError:
		return None


# resolved once at startup so the app stays agnostic of the actual account name
ALLOWED_USERNAME = _resolve_allowed_username(ALLOWED_UID)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 300
_TAG_KEYS = {"category", "language", "type"}
_SAFE_VALUE_RE = re.compile(r"^[^\n\r]{1,100}$")

# best-effort in-memory throttling; fine as long as mod_wsgi runs a single process
_login_attempts = {}


def load_admin_config():
	config_path = Path(
		os.environ.get("RB_LIBRARY_ADMIN_CONFIG", Path(__file__).resolve().parent / "admin-config.json")
	)
	defaults = {
		"secret_key": None,
		"admin_enabled": True,
		"filebrowser_enabled": False,
		"filebrowser_url": "",
		"session_lifetime_minutes": 30,
		# set to false only for local/plain-http testing; the production vhost must serve HTTPS
		"session_cookie_secure": True,
	}
	if config_path.exists():
		with config_path.open("r", encoding="utf-8") as f:
			defaults.update(json.load(f))
	if not defaults["secret_key"]:
		raise RuntimeError(
			f"Missing 'secret_key' in {config_path}. Generate one with: "
			"python3 -c \"import secrets; print(secrets.token_hex(32))\""
		)
	return defaults


config = load_admin_config()

app = Flask(__name__)
app.secret_key = config["secret_key"]
app.config.update(
	SESSION_COOKIE_HTTPONLY=True,
	SESSION_COOKIE_SAMESITE="Strict",
	SESSION_COOKIE_SECURE=config["session_cookie_secure"],
	PERMANENT_SESSION_LIFETIME=config["session_lifetime_minutes"] * 60,
)


@app.after_request
def _set_security_headers(response):
	response.headers["X-Content-Type-Options"] = "nosniff"
	response.headers["X-Frame-Options"] = "DENY"
	response.headers["Referrer-Policy"] = "same-origin"
	return response


def _client_ip():
	return request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"


def _is_locked_out(ip):
	attempt = _login_attempts.get(ip)
	if not attempt:
		return False
	count, first_ts = attempt
	if count < LOGIN_MAX_ATTEMPTS:
		return False
	if time.time() - first_ts > LOGIN_LOCKOUT_SECONDS:
		_login_attempts.pop(ip, None)
		return False
	return True


def _register_failed_attempt(ip):
	count, first_ts = _login_attempts.get(ip, (0, time.time()))
	_login_attempts[ip] = (count + 1, first_ts)


def require_login(view):
	@wraps(view)
	def wrapped(*args, **kwargs):
		if not config["admin_enabled"]:
			session.clear()
			return jsonify({"error": "admin interface disabled"}), 403
		if not session.get("authenticated"):
			return jsonify({"error": "authentication required"}), 401
		return view(*args, **kwargs)

	return wrapped


def require_csrf(view):
	@wraps(view)
	def wrapped(*args, **kwargs):
		token = request.headers.get("X-CSRF-Token")
		if not token or token != session.get("csrf_token"):
			return jsonify({"error": "invalid csrf token"}), 403
		return view(*args, **kwargs)

	return wrapped


@app.post("/login")
def login():
	if not config["admin_enabled"]:
		return jsonify({"error": "admin interface disabled"}), 403

	ip = _client_ip()
	if _is_locked_out(ip):
		return jsonify({"error": "too many attempts, try again later"}), 429

	if not ALLOWED_USERNAME:
		return jsonify({"error": f"server misconfigured: no system account with uid {ALLOWED_UID}"}), 500

	data = request.get_json(silent=True) or {}
	username = data.get("username", "")
	password = data.get("password", "")

	# only the system account matching ALLOWED_UID is allowed, whatever the input
	if username != ALLOWED_USERNAME:
		_register_failed_attempt(ip)
		return jsonify({"error": "invalid credentials"}), 401

	if pam is None:
		return jsonify({"error": "server misconfigured: pam module unavailable"}), 500

	if not pam.pam().authenticate(username, password, service="login"):
		_register_failed_attempt(ip)
		return jsonify({"error": "invalid credentials"}), 401

	_login_attempts.pop(ip, None)
	session.clear()
	session.permanent = True
	session["authenticated"] = True
	session["csrf_token"] = os.urandom(16).hex()
	return jsonify({"ok": True, "csrf_token": session["csrf_token"]})


@app.post("/logout")
def logout():
	session.clear()
	return jsonify({"ok": True})


@app.get("/config")
def get_config():
	return jsonify(
		{
			"admin_enabled": config["admin_enabled"],
			"filebrowser_enabled": config["filebrowser_enabled"],
			"filebrowser_url": config["filebrowser_url"],
		}
	)


@app.get("/scan")
@require_login
def scan():
	custom_lib = ensure_default_lists(load_library(CUSTOM_LIBRARY_PATH))
	_, custom_pdfs = find_pdfs(ROOT_DIR)
	new_files = [pdf for pdf in custom_pdfs if not is_present(custom_lib, pdf)]
	return jsonify({"files": new_files})


@app.get("/tags")
@require_login
def get_tags():
	main_lib = load_library(LIBRARY_PATH)
	custom_lib = ensure_default_lists(load_library(CUSTOM_LIBRARY_PATH))
	tags = {}
	for key in ("category", "language", "type"):
		main_values = main_lib.get(key, []) or []
		custom_values = custom_lib.get(key, []) or []
		# keep the main library order first, then any custom-only extra values
		tags[key] = list(main_values) + [v for v in custom_values if v not in main_values]
	return jsonify(tags)


@app.post("/tags")
@require_login
@require_csrf
def add_tag():
	data = request.get_json(silent=True) or {}
	tag_key = data.get("key")
	value = (data.get("value") or "").strip()

	if tag_key not in _TAG_KEYS:
		return jsonify({"error": "invalid tag key"}), 400
	if not value or not _SAFE_VALUE_RE.match(value):
		return jsonify({"error": "invalid tag value"}), 400

	# new values are only ever written to custom-library.json, never to library.json
	custom_lib = ensure_default_lists(load_library(CUSTOM_LIBRARY_PATH))
	values = custom_lib.setdefault(tag_key, [])
	if value not in values:
		values.append(value)
		save_library(custom_lib, CUSTOM_LIBRARY_PATH)
	return jsonify({"ok": True, "values": values})


@app.post("/entries")
@require_login
@require_csrf
def save_entries():
	data = request.get_json(silent=True) or {}
	entries = data.get("entries")
	if not isinstance(entries, list) or not entries:
		return jsonify({"error": "no entries provided"}), 400

	custom_lib = ensure_default_lists(load_library(CUSTOM_LIBRARY_PATH))
	_, custom_pdfs = find_pdfs(ROOT_DIR)
	custom_pdfs_set = set(custom_pdfs)

	main_lib = load_library(LIBRARY_PATH)
	known_tags = {}
	for key in _TAG_KEYS:
		known_tags[key] = set(custom_lib.get(key, []) or []) | set(main_lib.get(key, []) or [])

	saved = []
	for entry in entries:
		file_id = entry.get("id", "")
		name = (entry.get("name") or "").strip()
		category = entry.get("category", "")
		language = entry.get("language", "")
		type_value = entry.get("type", "")

		# only accept filenames that were actually found under PDF/custom
		if file_id not in custom_pdfs_set:
			return jsonify({"error": f"unknown file: {file_id}"}), 400
		if is_present(custom_lib, file_id):
			continue
		if not name:
			return jsonify({"error": f"name required for {file_id}"}), 400
		if category not in known_tags["category"] or language not in known_tags["language"] or type_value not in known_tags["type"]:
			return jsonify({"error": f"invalid tag values for {file_id}"}), 400

		key = next_key(custom_lib)
		custom_lib.setdefault("file_list", {})[key] = {
			"id": file_id,
			"name": name,
			"category": category,
			"language": language,
			"type": type_value,
		}
		saved.append(file_id)

	if saved:
		save_library(custom_lib, CUSTOM_LIBRARY_PATH)

	return jsonify({"ok": True, "saved": saved})


if __name__ == "__main__":
	app.run(debug=False)
