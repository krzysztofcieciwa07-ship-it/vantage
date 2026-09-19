#!/usr/bin/env python3
import argparse
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "evidence/vantage-verification.txt"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def parse(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            out[key] = value
    return out

def verify(evidence, expected_commit=None):
    if not evidence.is_file():
        raise SystemExit("INDEPENDENT_VERIFY: evidence file missing")
    values = parse(evidence)
    for key in ("commit", "afe_vantage_sha256", "tests_sha256"):
        if key not in values:
            raise SystemExit("INDEPENDENT_VERIFY: missing field " + key)
    expected = expected_commit or os.environ.get("GITHUB_SHA")
    if expected and values["commit"] != expected:
        raise SystemExit("INDEPENDENT_VERIFY: commit mismatch")
    checks = {
        "afe_vantage_sha256": sha256(ROOT / "afe_vantage.py"),
        "tests_sha256": sha256(ROOT / "tests/test_afe_vantage.py"),
    }
    for key, actual in checks.items():
        if values[key] != actual:
            raise SystemExit("INDEPENDENT_VERIFY: " + key + " mismatch")
    print("INDEPENDENT_VERIFY: PASS")
    print("commit=" + values["commit"])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--expected-commit")
    args = parser.parse_args()
    verify(args.evidence, args.expected_commit)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
