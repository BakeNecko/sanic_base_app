PROJECT_NAME = my_app
DOCKER_COMPOSE = docker compose
TEST_COMMAND = pytest
ENV_FILE = .env

.PHONY: all
all: run

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
	$(DOCKER_COMPOSE) -p $(PROJECT_NAME) logs -f 
