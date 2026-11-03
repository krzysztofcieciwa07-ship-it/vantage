"""Actual loopback HTTP transport for the signed Vantage AFE service."""
import hashlib
import hmac
import json
from threading import Thread
import uuid
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from http.server import ThreadingHTTPServer

from vantage_decision_api import DecisionAuthority, _handler_for, canonical_json


def test_authenticated_http_service_signs_real_policy_and_rejects_replay(tmp_path):
    private = Ed25519PrivateKey.generate()
    secret = b"test-only-vantage-http-secret-0123456789" * 2
    authority = DecisionAuthority(secret, private, str(tmp_path / "http-replay.db"),
                                  source_commit="c" * 40)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(authority))
    server.daemon_threads = True
    server.timeout = 3
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(url + "/health", timeout=3) as response:
            assert response.status == 200
        body = {
            "schema": "ola.vantage.request.v1",
            "operation_id": str(uuid.uuid4()),
            "tenant_id": str(uuid.uuid4()),
            "action": "safe_expression",
            "task_text": "Please summarize a contract.",
            "task_sha256": hashlib.sha256(b"Please summarize a contract.").hexdigest(),
        }
        data = canonical_json(body).encode()
        import time
        now = int(time.time())
        nonce = uuid.uuid4().hex
        signature = hmac.new(secret,
                             f"v1\n{now}\n{nonce}\n{hashlib.sha256(data).hexdigest()}".encode(),
                             hashlib.sha256).hexdigest()
        request = urllib.request.Request(url + "/v1/decisions", method="POST", data=data,
                                         headers={
                                             "Content-Type": "application/json",
                                             "X-OLA-Timestamp": str(now),
                                             "X-OLA-Nonce": nonce,
                                             "X-OLA-Signature": signature,
                                         })
        with urllib.request.urlopen(request, timeout=4) as response:
            assert response.status == 200
            decision = json.load(response)
        assert decision["receipt"]["verdict"] == "ALLOW"
        assert decision["receipt"]["operation_id"] == body["operation_id"]
        with __import__("pytest").raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(request, timeout=4)
        assert exc.value.code == 409
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=4)
