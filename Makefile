ENV_FILE := src/core/conf/envs/.env.dev
RUN=docker compose --env-file ${ENV_FILE} run --rm news
NONE_IMAGES=docker images -f "dangling=true" -q
RUNNING_CONTAINERS=docker ps -q
COMPOSE_FILE := docker-compose.yml
all:
	docker compose -f ${COMPOSE_FILE} build
	docker rmi $$(${NONE_IMAGES}) -f

run:
	docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE} up

stop:
	docker compose -f ${COMPOSE_FILE} down

shell:
	${RUN} /bin/bash

migrate:
	${RUN} alembic upgrade head

revision:
	${RUN} alembic revision --autogenerate
