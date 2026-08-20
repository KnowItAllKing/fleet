.PHONY: check list status sync sync-dry-run targets test

check:
	python3 scripts/skills.py check

list:
	python3 scripts/skills.py list

targets:
	python3 scripts/skills.py targets

status:
	python3 scripts/skills.py status

sync: check
	python3 scripts/skills.py sync

sync-dry-run: check
	python3 scripts/skills.py sync --dry-run

test: check
	python3 -m unittest discover -s tests -v
