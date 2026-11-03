"""Resolve exact GitHub Sigstore workflow SAN from a trusted workflow_run event.

Fail closed for ambiguous PR linkage, non-main direct runs and mismatched commits.
Never accept wildcard certificate identities.
"""
import argparse
import json
import re
from pathlib import Path

REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
COMMIT_PATTERN = re.compile(r"[a-fA-F0-9]{40}\Z")
WORKFLOW_PATH = ".github/workflows/verify.yml"


def resolve(event, repository):
    if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("invalid target repository")
    if not isinstance(event, dict) or not isinstance(event.get("repository"), dict):
        raise ValueError("missing triggering repository")
    if event["repository"].get("full_name") != repository:
        raise ValueError("triggering repository mismatch")
    run = event.get("workflow_run")
    if not isinstance(run, dict) or not isinstance(run.get("repository"), dict):
        raise ValueError("missing source workflow run")
    if run["repository"].get("full_name") != repository:
        raise ValueError("source repository mismatch")
    if (run.get("name") != "Vantage Verify" or run.get("status") != "completed"
            or run.get("conclusion") != "success"):
        raise ValueError("source workflow is not the required successful run")
    if run.get("path") not in (None, WORKFLOW_PATH):
        raise ValueError("source workflow path mismatch")
    sha = run.get("head_sha")
    if not isinstance(sha, str) or not COMMIT_PATTERN.fullmatch(sha):
        raise ValueError("invalid source commit")
    run_id = run.get("id")
    if type(run_id) is not int or run_id < 1:
        raise ValueError("invalid source run ID")
    run_attempt = run.get("run_attempt")
    if type(run_attempt) is not int or run_attempt < 1:
        raise ValueError("invalid source run attempt")

    event_type = run.get("event")
    if event_type == "pull_request":
        pull_requests = run.get("pull_requests")
        if not isinstance(pull_requests, list) or len(pull_requests) != 1:
            raise ValueError("pull request identity missing or ambiguous")
        pr = pull_requests[0]
        if not isinstance(pr, dict) or type(pr.get("number")) is not int or pr["number"] < 1:
            raise ValueError("invalid pull request number")
        head = pr.get("head")
        if isinstance(head, dict) and head.get("sha") and head["sha"] != sha:
            raise ValueError("pull request source commit mismatch")
        ref = f"refs/pull/{pr['number']}/merge"
    elif event_type in ("push", "workflow_dispatch"):
        if run.get("head_branch") != "main":
            raise ValueError("only signed main direct runs are eligible")
        ref = "refs/heads/main"
    else:
        raise ValueError("unsupported source event")

    return {
        "EXPECTED_IDENTITY": f"https://github.com/{repository}/{WORKFLOW_PATH}@{ref}",
        "EXPECTED_COMMIT": sha,
        "EXPECTED_RUN_ID": str(run_id),
        "EXPECTED_RUN_ATTEMPT": str(run_attempt),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        values = resolve(json.loads(args.event.read_text(encoding="utf-8")), args.repository)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(1, f"BLOCKED: {exc}\n")
    for key, value in values.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
