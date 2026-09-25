USER_SEED ?= 12345
.PHONY: test verify replay run up load kill probe probe-duration assert hidden score down clean

test:
	python3 -m pytest -q

verify:
	python3 -m ci.evidence_vault verify

replay:
	python3 -m ci.replay

run:
	USER_SEED=$(USER_SEED) python3 -m ci.gen_incident --seed $(USER_SEED)
	@echo "CFR-18 incident generated."
	@echo "Next: make up load kill probe-duration assert score"

up:
	docker compose down -v --remove-orphans >/dev/null 2>&1 || true
	docker compose up -d --build
	@until curl -fsS http://localhost:8098/health >/dev/null; do sleep 1; done
	@echo "API healthy"

load:
	@for i in $$(seq 1 8); do curl -fsS -X POST http://localhost:8098/enqueue -H 'content-type: application/json' -d "{\"id\":$$i}" >/dev/null; done

kill:
	docker compose stop worker

probe:
	DURATION=$$(printenv DURATION 2>/dev/null || echo 120) sh scripts/probe.sh

probe-duration:
	DURATION=120 sh scripts/probe.sh

assert:
	sh ci/assertions.sh

hidden:
	python3 -m ci.hidden_check --seed $(USER_SEED) --elapsed 120

score:
	python3 -m ci.score

down:
	docker compose down -v --remove-orphans

clean:
	docker compose down -v --remove-orphans || true
	rm -f data/*.jsonl evidence/*.json evidence/.chain.jsonl
