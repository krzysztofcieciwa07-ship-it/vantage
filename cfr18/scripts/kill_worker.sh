#!/bin/sh
set -eu
docker compose stop worker
python3 -m ci.evidence_vault append worker_stopped --data '{"actor":"scenario"}'
