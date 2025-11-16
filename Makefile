PYTHON := python

.PHONY: run test install docker-build docker-run

install:
	uv sync

run:
	$(PYTHON) -m bot.main

test:
	pytest -q

docker-build:
	docker build -t neuro-symbolic-bot .

docker-run:
	docker run --rm --env-file .env neuro-symbolic-bot


