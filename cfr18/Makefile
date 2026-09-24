test:
	python3 -m pytest -q
incident:
	python3 -m ci.gen_incident --seed 12345
verify:
	python3 -m ci.evidence_vault verify
replay:
	python3 -m ci.replay
score:
	python3 -m ci.score
