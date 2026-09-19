#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(record):
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8")

def build(commit, evidence, replay, previous_hash="0" * 64):
    record = {
        "version": 1,
        "commit": commit,
        "evidence_sha256": sha256(evidence),
        "replay_sha256": sha256(replay),
        "previous_hash": previous_hash,
    }
    record["record_hash"] = hashlib.sha256(canonical(record)).hexdigest()
    return record

def verify(path, expected_commit=None):
    record = json.loads(path.read_text(encoding="utf-8"))
    required = ("version", "commit", "evidence_sha256", "replay_sha256", "previous_hash", "record_hash")
    for key in required:
        if key not in record:
            raise SystemExit("PROVENANCE_ANCHOR: missing field " + key)
    expected = dict(record)
    actual = expected.pop("record_hash")
    calculated = hashlib.sha256(canonical(expected)).hexdigest()
    if actual != calculated:
        raise SystemExit("PROVENANCE_ANCHOR: record_hash mismatch")
    if expected_commit and record["commit"] != expected_commit:
        raise SystemExit("PROVENANCE_ANCHOR: commit mismatch")
    print("PROVENANCE_ANCHOR: PASS")
    print("record_hash=" + actual)
    print("commit=" + record["commit"])

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--commit", required=True)
    b.add_argument("--evidence", type=Path, required=True)
    b.add_argument("--replay", type=Path, required=True)
    b.add_argument("--previous-hash", default="0" * 64)
    b.add_argument("--output", type=Path, required=True)
    v = sub.add_parser("verify")
    v.add_argument("--anchor", type=Path, required=True)
    v.add_argument("--expected-commit")
    args = p.parse_args()
    if args.command == "build":
        args.output.write_text(
            json.dumps(build(args.commit, args.evidence, args.replay, args.previous_hash), sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print("PROVENANCE_ANCHOR: CREATED")
    else:
        verify(args.anchor, args.expected_commit)

if __name__ == "__main__":
    raise SystemExit(main())
