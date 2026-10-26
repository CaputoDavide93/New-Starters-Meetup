# One entry point for the checks CI runs. `make check` before every push.
PYTHON := .venv/bin/python

.PHONY: venv test lint diagram check build social-preview

venv: ## Python 3.13 environment with the locked layer dependencies, boto3, pytest and ruff
	python3.13 -m venv .venv
	.venv/bin/pip install -q -r requirements.txt
	.venv/bin/pip install -q boto3 pytest ruff

test: ## The pytest suite (Secrets Manager, Slack, Google and Graph are stubbed)
	$(PYTHON) -m pytest -q tests

lint: ## ruff, same rules as CI
	$(PYTHON) -m ruff check --select E4,E7,E9,F src scripts tests

diagram: ## Redraw docs/assets/*.svg
	python3 tools/gen_diagram.py

check: lint test ## Everything CI checks
	python3 tools/gen_diagram.py --check
	sh tools/brand/check-icon.sh

build: ## Build the three Lambda ZIPs into dist/ (needs network and zip)
	./scripts/build.sh

social-preview: ## Redraw docs/assets/social-preview.png (needs Google Chrome and pillow)
	python3 tools/brand/brand_kit.py social --repo New-Starters-Meetup --name "New Starters MeetUp" --tagline "One Slack command books coffee and buddy intros for new starters" --chip "/newintro" --chip "Google Calendar" --chip "Azure AD" --chip "AWS Lambda" --icon docs/assets/brand/icon.svg
