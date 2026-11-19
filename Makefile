run:
	./run.sh examples/preso

video:
	./run.sh examples/preso --format video

install:
	./run.sh --help
	.venv/bin/python -m playwright install chromium 2>/dev/null || .venv/Scripts/python -m playwright install chromium

format:
	black -q .

lint:
	ruff check .

test:
	python -m pytest -q

.PHONY: run video install format lint test
