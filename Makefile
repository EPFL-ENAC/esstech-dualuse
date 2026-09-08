install:
	cd backend && make install
	cd frontend && npm install
	test -f .env || cp .env.example .env

lint:
	uvx lefthook run pre-commit --all-files

run-db:
	docker compose up -d

stop-db:
	docker compose down

reset-db:
	docker compose down --volumes
	docker compose up -d

run-backend:
	cd backend && make run

run-frontend:
	cd frontend && npm run dev

test:
	cd backend && make test

db-upgrade:
	cd backend && make db-upgrade

db-downgrade:
	cd backend && make db-downgrade

db-revision:
	cd backend && make db-revision name="$(name)"

db-seed:
	cd backend && make db-seed
