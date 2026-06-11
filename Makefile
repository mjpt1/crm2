# ─── Makefile — دستورات رایج ───

.PHONY: up down build migrate superuser logs shell restart

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart web

migrate:
	docker compose run --rm web python manage.py migrate

superuser:
	docker compose run --rm web python manage.py createsuperuser

static:
	docker compose run --rm web python manage.py collectstatic --noinput

logs:
	docker compose logs -f web

shell:
	docker compose run --rm web python manage.py shell

db-shell:
	docker compose exec db psql -U crm_user -d crm_db

# راه‌اندازی محیط توسعه محلی (بدون Docker)
dev-install:
	pip install -r requirements.txt

dev-run:
	python manage.py runserver 0.0.0.0:8000

dev-migrate:
	python manage.py migrate

dev-static:
	python manage.py collectstatic --noinput
