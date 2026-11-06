"""Authenticated Vantage AFE decision service with Ed25519 receipts.

This signs REAL verdicts from the repo's AFE engine, not a caller-provided
ALLOW flag. The default bind is loopback only. Treat it as a pilot policy
gate; the heuristic classifier is NOT sufficient for production authority.
"""
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

from afe_vantage import AFE, Task, Verdict


REQUEST_FIELDS = frozenset({
    "schema", "operation_id", "tenant_id", "action", "task_sha256", "task_text"
})
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_SHA = re.compile(r"[0-9a-f]{40}\Z")
NONCE = re.compile(r"[a-f0-9]{32}\Z")
MAX_BYTES = 8192
ALLOWED_ACTIONS = frozenset({"safe_expression"})
SKEW_SECONDS = 30
RECEIPT_LIFETIME_SECONDS = 30


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def receipt_public_key_id(key: Ed25519PublicKey) -> str:
    raw = key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return "vantage-ed25519-sha256-" + hashlib.sha256(raw).hexdigest()[:32]


def _canonical_uuid(text):
    if not isinstance(text, str):
        return False
    try:
        return str(uuid.UUID(text)) == text
    except (ValueError, AttributeError):
        return False


class DecisionAuthority:
    def __init__(self, shared_secret: bytes, private_key: Ed25519PrivateKey,
                 replay_db: str, *, source_commit: str):
        if not isinstance(shared_secret, bytes) or len(shared_secret) < 32:
            raise ValueError("Vantage request HMAC secret must be 32+ bytes")
        if not isinstance(private_key, Ed25519PrivateKey):
            raise ValueError("Ed25519 private key required")
        if not isinstance(source_commit, str) or not SOURCE_SHA.fullmatch(source_commit):
            raise ValueError("Exact Vantage source commit required")
        self.secret = shared_secret
        self.private_key = private_key
        self.key_id = receipt_public_key_id(private_key.public_key())
        self.source_commit = source_commit
        self.replay_db = replay_db
        self.afe = AFE()
        with sqlite3.connect(replay_db, timeout=15) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS consumed_nonces ("
                         "nonce TEXT PRIMARY KEY, issued_at INTEGER NOT NULL)")

    def _consume_nonce(self, nonce, issued_at):
        # The durable SQLite UNIQUE constraint prevents replay across threads
        # and service restarts. Fail closed on database outage.
        try:
            with sqlite3.connect(self.replay_db, timeout=15) as conn:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute("DELETE FROM consumed_nonces WHERE issued_at < ?",
                             (issued_at - 600,))
                conn.execute("INSERT INTO consumed_nonces(nonce, issued_at) VALUES (?, ?)",
                             (nonce, issued_at))
            return True
        except sqlite3.IntegrityError:
            return False

    def decide(self, raw: bytes, headers, *, now=None):
        now = int(time.time()) if now is None else int(now)
        if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
            return 400, {"error": "invalid request size"}
        try:
            timestamp_text = headers.get("X-OLA-Timestamp", "")
            nonce = headers.get("X-OLA-Nonce", "")
            signature = headers.get("X-OLA-Signature", "")
            if not isinstance(timestamp_text, str) or not timestamp_text.isdigit():
                return 401, {"error": "authentication rejected"}
            timestamp = int(timestamp_text)
            if (not str(timestamp_text).isdigit() or not NONCE.fullmatch(nonce)
                    or not HEX_SHA256.fullmatch(signature)
                    or abs(now - timestamp) > SKEW_SECONDS):
                return 401, {"error": "authentication rejected"}
            digest = hashlib.sha256(raw).hexdigest()
            mac = hmac.new(
                self.secret, f"v1\n{timestamp}\n{nonce}\n{digest}".encode(),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(mac, signature):
                return 401, {"error": "authentication rejected"}
            payload = json.loads(raw)
            if (not isinstance(payload, dict) or set(payload) != REQUEST_FIELDS
                    or canonical_json(payload).encode("utf-8") != raw):
                return 400, {"error": "invalid canonical policy request"}
            task_text = payload["task_text"]
            if (payload["schema"] != "ola.vantage.request.v1"
                    or not _canonical_uuid(payload["operation_id"])
                    or not _canonical_uuid(payload["tenant_id"])
                    or not isinstance(task_text, str)
                    or not 1 <= len(task_text) <= 2000
                    or type(payload["action"]) is not str
                    or len(payload["action"]) > 80
                    or not isinstance(payload["task_sha256"], str)
                    or not HEX_SHA256.fullmatch(payload["task_sha256"])
                    or hashlib.sha256(task_text.encode()).hexdigest()
                       != payload["task_sha256"]):
                return 400, {"error": "invalid policy request contract"}
            # Mark nonce after all structural checks, before classification.
            if not self._consume_nonce(nonce, now):
                return 409, {"error": "replayed request"}
            decision = self.afe.run(
                Task(text=task_text, source="user_upload", task_type="security")
            )
            verdict = (decision.verdict.value
                       if payload["action"] in ALLOWED_ACTIONS else "BLOCK")
            receipt = {
                "schema": "ola.vantage.receipt.v1",
                "operation_id": payload["operation_id"],
                "tenant_id": payload["tenant_id"],
                "action": payload["action"],
                "task_sha256": payload["task_sha256"],
                "verdict": verdict,
                "detector_score": decision.detector_score,
                "incident_score": decision.incident_score,
                "sandbox_stability": decision.sandbox_stability,
                "classifier": "vantage.AFE",
                "source_commit": self.source_commit,
                "issued_at": now,
                "expires_at": now + RECEIPT_LIFETIME_SECONDS,
                "request_nonce": nonce,
                "signer_key_id": self.key_id,
                "trust_scope": "signed_heuristic_policy_only",
                "production_authorized": False,
            }
            signed = canonical_json(receipt).encode("utf-8")
            return 200, {
                "receipt": receipt,
                "signature": base64.b64encode(self.private_key.sign(signed)).decode("ascii"),
            }
        except (KeyError, TypeError, ValueError, UnicodeDecodeError):
            return 400, {"error": "invalid policy request"}


def _handler_for(authority):
    class Handler(BaseHTTPRequestHandler):
        server_version = "VantagePolicy/1"
        sys_version = ""

        def log_message(self, *args):
            # Never log URLs with possible credential fields, body or headers.
            return

        def _respond(self, status, obj):
            output = canonical_json(obj).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(output)))
            self.end_headers()
            self.wfile.write(output)

        def do_GET(self):
            if self.path == "/health":
                self._respond(200, {"status": "UP", "trust_scope": "local_pilot_only"})
            else:
                self._respond(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/decisions":
                self._respond(404, {"error": "not found"})
                return
            length = self.headers.get("Content-Length", "")
            if not length.isdecimal() or not 0 < int(length) <= MAX_BYTES:
                self._respond(413, {"error": "invalid body length"})
                return
            body = self.rfile.read(int(length))
            try:
                status, response = authority.decide(body, self.headers)
            except (OSError, sqlite3.Error):
                status, response = 503, {"error": "decision service unavailable"}
            self._respond(status, response)

    return Handler


def _load_authority():
    path = Path(os.environ["VANTAGE_ED25519_PRIVATE_KEY_FILE"])
    if not path.is_file() or path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError("private signing key must be a regular 0600 file")
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    secret = os.environ["VANTAGE_HMAC_SECRET"].encode("utf-8")
    return DecisionAuthority(
        secret, key, os.environ["VANTAGE_REPLAY_DB"],
        source_commit=os.environ["VANTAGE_SOURCE_COMMIT"],
    )


def main():
    authority = _load_authority()
    host = os.getenv("VANTAGE_BIND_HOST", "127.0.0.1")
    if host not in ("127.0.0.1", "::1") and os.getenv("VANTAGE_PRIVATE_NETWORK_BIND") != "1":
        raise ValueError("public Vantage listener refused; use private network and TLS gateway")
    port = int(os.getenv("VANTAGE_PORT", "18710"))
    server = ThreadingHTTPServer((host, port), _handler_for(authority))
    print("VANTAGE_DECISION_API_READY: signed pilot only; production NOT_AUTHORIZED",
          file=sys.stderr, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
