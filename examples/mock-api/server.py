#!/usr/bin/env python3
"""Deterministic local mock of the Customers API (examples/openapi/customers-api.yaml).

Standard library only. Data lives in memory and is lost when the server
stops. Intended ONLY for local demos and CI — never expose it publicly.

    python examples/mock-api/server.py --port 8000

Tokens are local, non-secret demo values and can be overridden with the
environment variables MOCK_API_USER_TOKEN / MOCK_API_ADMIN_TOKEN.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

DEFAULT_USER_TOKEN = "local-user-token"
DEFAULT_ADMIN_TOKEN = "local-admin-token"
EXPIRED_TOKEN = "local-expired-token"

NAME_MAX = 100
EMAIL_MAX = 254
CREDIT_MIN, CREDIT_MAX = 0, 50000
LIMIT_MIN, LIMIT_MAX, LIMIT_DEFAULT = 1, 100, 20
STATUSES = ("active", "suspended", "closed")
CREATE_STATUSES = ("active", "suspended")
ALLOWED_TRANSITIONS = {
    "active": {"active", "suspended", "closed"},
    "suspended": {"suspended", "active", "closed"},
    "closed": set(),  # terminal
}
WRITABLE_FIELDS = {"name", "email", "status", "credit_limit"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CUSTOMER_PATH_RE = re.compile(r"^/customers/([^/]+)$")
MAX_BODY_BYTES = 64 * 1024


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, details: Optional[List[dict]] = None,
                 headers: Optional[Dict[str, str]] = None):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.details = details or []
        self.headers = headers or {}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class Store:
    """Thread-safe in-memory customer store."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.customers: Dict[str, dict] = {}
        self.sequence = 0
        self.idempotency: Dict[str, Tuple[str, dict]] = {}

    def reset(self) -> None:
        with self.lock:
            self.customers.clear()
            self.idempotency.clear()
            self.sequence = 0

    def email_taken(self, email: str, exclude_id: Optional[str] = None) -> bool:
        lowered = email.lower()
        return any(c["email"].lower() == lowered and c["id"] != exclude_id for c in self.customers.values())


def validate_fields(body: Dict[str, Any], partial: bool) -> List[dict]:
    """Return a list of {field, issue} validation problems."""
    problems: List[dict] = []
    for key in body:
        if key not in WRITABLE_FIELDS:
            problems.append({"field": key, "issue": "unknown field"})
    required = () if partial else ("name", "email")
    for key in required:
        if key not in body:
            problems.append({"field": key, "issue": "required"})
    if "name" in body:
        name = body["name"]
        if not isinstance(name, str):
            problems.append({"field": "name", "issue": "must be a string"})
        elif not name.strip():
            problems.append({"field": "name", "issue": "must not be blank"})
        elif len(name.strip()) > NAME_MAX:
            problems.append({"field": "name", "issue": f"must be at most {NAME_MAX} characters"})
    if "email" in body:
        email = body["email"]
        if not isinstance(email, str):
            problems.append({"field": "email", "issue": "must be a string"})
        elif len(email) > EMAIL_MAX or not EMAIL_RE.match(email.strip()):
            problems.append({"field": "email", "issue": "must be a valid email address"})
    if "status" in body:
        allowed = STATUSES if partial else CREATE_STATUSES
        if body["status"] not in allowed:
            problems.append({"field": "status", "issue": f"must be one of {list(allowed)}"})
    if "credit_limit" in body:
        value = body["credit_limit"]
        if isinstance(value, bool) or not isinstance(value, int):
            problems.append({"field": "credit_limit", "issue": "must be an integer"})
        elif not CREDIT_MIN <= value <= CREDIT_MAX:
            problems.append({"field": "credit_limit", "issue": f"must be between {CREDIT_MIN} and {CREDIT_MAX}"})
    return problems


class Handler(BaseHTTPRequestHandler):
    server_version = "CustomersMock/0.1"
    store: Store  # injected by make_server
    user_token: str
    admin_token: str

    # ------------------------------------------------------------ plumbing
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
        if os.environ.get("MOCK_API_VERBOSE"):
            super().log_message(format, *args)

    def _send(self, status: int, payload: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> None:
        data = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.send_response(status)
        if payload is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if data:
            self.wfile.write(data)

    def _error(self, err: ApiError) -> None:
        body = {"error": {"code": err.code, "message": err.message, "details": err.details}}
        self._send(err.status, body, err.headers)

    def _dispatch(self, method: str) -> None:
        try:
            self._route(method)
        except ApiError as err:
            self._error(err)
        except Exception:  # pragma: no cover - defensive, never leak internals
            self._error(ApiError(500, "internal_error", "Unexpected server error"))

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_PATCH(self) -> None:  # noqa: N802
        self._dispatch("PATCH")

    def do_DELETE(self) -> None:  # noqa: N802
        self._dispatch("DELETE")

    def do_PUT(self) -> None:  # noqa: N802
        self._dispatch("PUT")

    # ------------------------------------------------------------- helpers
    def _auth(self, admin: bool = False) -> None:
        header = self.headers.get("Authorization", "")
        challenge = {"WWW-Authenticate": "Bearer"}
        if not header.startswith("Bearer ") or not header[7:].strip():
            raise ApiError(401, "unauthorized", "Missing or malformed bearer token", headers=challenge)
        token = header[7:].strip()
        if token == EXPIRED_TOKEN:
            raise ApiError(401, "token_expired", "Token has expired", headers=challenge)
        if token not in (self.user_token, self.admin_token):
            raise ApiError(401, "unauthorized", "Invalid token", headers=challenge)
        if admin and token != self.admin_token:
            raise ApiError(403, "forbidden", "Admin role required")

    def _json_body(self) -> Dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type != "application/json":
            raise ApiError(415, "unsupported_media_type", "Content-Type must be application/json")
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            raise ApiError(413, "payload_too_large", f"Body exceeds {MAX_BODY_BYTES} bytes")
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "malformed_json", "Request body is not valid JSON") from None
        if not isinstance(body, dict):
            raise ApiError(400, "malformed_json", "Request body must be a JSON object")
        return body

    @staticmethod
    def _int_param(params: Dict[str, List[str]], name: str, default: int, low: int,
                   high: Optional[int], problems: List[dict]) -> int:
        if name not in params:
            return default
        raw = params[name][0]
        if not re.fullmatch(r"-?\d+", raw):
            problems.append({"field": name, "issue": "must be an integer"})
            return default
        value = int(raw)
        if value < low or (high is not None and value > high):
            bounds = f"between {low} and {high}" if high is not None else f">= {low}"
            problems.append({"field": name, "issue": f"must be {bounds}"})
        return value

    # -------------------------------------------------------------- routes
    def _route(self, method: str) -> None:
        url = urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        if path == "/health":
            if method != "GET":
                raise ApiError(405, "method_not_allowed", "Method not allowed", headers={"Allow": "GET"})
            self._send(200, {"status": "ok"})
            return
        if path == "/customers":
            if method == "GET":
                self._list(parse_qs(url.query))
            elif method == "POST":
                self._create()
            else:
                raise ApiError(405, "method_not_allowed", "Method not allowed", headers={"Allow": "GET, POST"})
            return
        match = CUSTOMER_PATH_RE.match(path)
        if match:
            customer_id = match.group(1)
            if method == "GET":
                self._get(customer_id)
            elif method == "PATCH":
                self._update(customer_id)
            elif method == "DELETE":
                self._delete(customer_id)
            else:
                raise ApiError(405, "method_not_allowed", "Method not allowed",
                               headers={"Allow": "GET, PATCH, DELETE"})
            return
        raise ApiError(404, "not_found", "Route not found")

    def _list(self, params: Dict[str, List[str]]) -> None:
        self._auth()
        problems: List[dict] = []
        limit = self._int_param(params, "limit", LIMIT_DEFAULT, LIMIT_MIN, LIMIT_MAX, problems)
        offset = self._int_param(params, "offset", 0, 0, None, problems)
        status = params.get("status", [None])[0]
        if status is not None and status not in STATUSES:
            problems.append({"field": "status", "issue": f"must be one of {list(STATUSES)}"})
        if problems:
            raise ApiError(422, "validation_error", "Invalid query parameters", problems)
        with self.store.lock:
            items = sorted(self.store.customers.values(), key=lambda c: c["id"])
        if status:
            items = [c for c in items if c["status"] == status]
        self._send(200, {"data": items[offset:offset + limit],
                         "pagination": {"limit": limit, "offset": offset, "total": len(items)}})

    def _create(self) -> None:
        self._auth()
        body = self._json_body()
        key = self.headers.get("Idempotency-Key")
        if key is not None and not (1 <= len(key) <= 64):
            raise ApiError(422, "validation_error", "Invalid Idempotency-Key",
                           [{"field": "Idempotency-Key", "issue": "must be 1-64 characters"}])
        fingerprint = json.dumps(body, sort_keys=True)
        problems = validate_fields(body, partial=False)
        if problems:
            raise ApiError(422, "validation_error", "Request validation failed", problems)
        with self.store.lock:
            if key is not None and key in self.store.idempotency:
                stored_fingerprint, stored = self.store.idempotency[key]
                if stored_fingerprint != fingerprint:
                    raise ApiError(422, "idempotency_key_reused",
                                   "Idempotency-Key was already used with a different body")
                self._send(201, stored, {"Location": f"/customers/{stored['id']}",
                                         "Idempotent-Replayed": "true"})
                return
            email = body["email"].strip()
            if self.store.email_taken(email):
                raise ApiError(409, "email_conflict", "A customer with this email already exists")
            self.store.sequence += 1
            now = _now()
            customer = {
                "id": f"cus_{self.store.sequence:06d}",
                "name": body["name"].strip(),
                "email": email,
                "status": body.get("status", "active"),
                "credit_limit": body.get("credit_limit", 0),
                "created_at": now,
                "updated_at": now,
            }
            self.store.customers[customer["id"]] = customer
            if key is not None:
                self.store.idempotency[key] = (fingerprint, dict(customer))
        self._send(201, customer, {"Location": f"/customers/{customer['id']}"})

    def _find(self, customer_id: str) -> dict:
        customer = self.store.customers.get(customer_id)
        if customer is None:
            raise ApiError(404, "not_found", f"Customer {customer_id} not found")
        return customer

    def _get(self, customer_id: str) -> None:
        self._auth()
        with self.store.lock:
            customer = dict(self._find(customer_id))
        self._send(200, customer)

    def _update(self, customer_id: str) -> None:
        self._auth()
        body = self._json_body()
        if not body:
            raise ApiError(422, "validation_error", "At least one field is required",
                           [{"field": "body", "issue": "must not be empty"}])
        problems = validate_fields(body, partial=True)
        if problems:
            raise ApiError(422, "validation_error", "Request validation failed", problems)
        with self.store.lock:
            customer = self._find(customer_id)
            if customer["status"] == "closed":
                raise ApiError(409, "invalid_state_transition", "Closed customers cannot be modified")
            new_status = body.get("status", customer["status"])
            if new_status not in ALLOWED_TRANSITIONS[customer["status"]]:
                raise ApiError(409, "invalid_state_transition",
                               f"Cannot change status from {customer['status']} to {new_status}")
            if "email" in body and self.store.email_taken(body["email"].strip(), exclude_id=customer_id):
                raise ApiError(409, "email_conflict", "A customer with this email already exists")
            for key, value in body.items():
                customer[key] = value.strip() if isinstance(value, str) else value
            customer["updated_at"] = _now()
            result = dict(customer)
        self._send(200, result)

    def _delete(self, customer_id: str) -> None:
        self._auth(admin=True)
        with self.store.lock:
            self._find(customer_id)
            del self.store.customers[customer_id]
        self._send(204)


def make_server(host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    """Create (but do not start) a server. Port 0 picks a free port."""
    handler = type("BoundHandler", (Handler,), {
        "store": Store(),
        "user_token": os.environ.get("MOCK_API_USER_TOKEN", DEFAULT_USER_TOKEN),
        "admin_token": os.environ.get("MOCK_API_ADMIN_TOKEN", DEFAULT_ADMIN_TOKEN),
    })
    server = ThreadingHTTPServer((host, port), handler)
    server.daemon_threads = True
    return server


def start_in_thread(host: str = "127.0.0.1", port: int = 0) -> Tuple[ThreadingHTTPServer, str]:
    """Start a server in a daemon thread and return (server, base_url)."""
    server = make_server(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_host, actual_port = server.server_address[:2]
    return server, f"http://{actual_host}:{actual_port}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Customers API mock.")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port (default 8000)")
    args = parser.parse_args()
    server = make_server(args.host, args.port)
    print(f"Customers mock API listening on http://{args.host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
