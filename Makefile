PROJECT_NAME = my_app
DOCKER_COMPOSE = docker compose

.PHONY: all
all: start sleep migrate dump

# Иногда миграции alembic могут запуститься до реального старта postgresql
.PHONY: sleep
sleep:
	sleep 2

.PHONY: start
start:
	@echo "Запуск контейнеров..."
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) up -d --build

.PHONY: run
run:
	@echo "Запуск контейнеров..."
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) up --build

.PHONY: migrate
migrate:
	@echo "Выполнение миграций Alembic..."
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) exec web alembic -c /app/alembic.ini  upgrade head 

.PHONY: dump
dump:
	@echo "Загрузка пользователей.."
	cat dumps/user_dump.sql | docker exec -i web_psql  psql -U myuser -d mydatabase

.PHONY: clean_db
clean_db:
	@echo "Очистка БД"
	cat dumps/clean.sql | docker exec -i web_psql  psql -U myuser -d mydatabase

.PHONY: shell
shell:
	@echo "Переход в контейнер web..."
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) exec web sh


.PHONY: test
test:
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) -f docker-compose.test.yml up --build

.PHONY: down
down:
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) down

.PHONY: psql
psql:
	docker exec -it web_psql  psql -U myuser -d mydatabase psql

.PHONY: clean
clean: down
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) rm -f 

.PHONY: logs
logs:
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) logs -f --tail 50

.PHONY: help
help:
	@echo "Доступные команды:"
	@echo "  run      - Запуск контейнеров в режиме отладки"
	@echo "  start    - Запуск контейнеров в фоновом режиме"
	@echo "  down     - Остановить все контейнеры"
	@echo "  migrate  - Применить миграции Alemibc"
	@echo "  dump     - Загрузить дамп пользовательских данных"
	@echo "  shell    - Зайти в sanic-container"
	@echo "  psql     - Зайти в postgres-container"
	@echo "  clean    - Сначала down затем rm -f"
	@echo "  clean_db - Очистить БД"
	@echo "  logs     - Последние логи контейнеров"
