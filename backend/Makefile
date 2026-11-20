# --locked installs exactly the versions in uv.lock (and fails if the lock is
# stale), so CI checks the same libraries as every developer machine.
install:
	uv sync --locked --extra dev --python 3.13

run:
	uv run uvicorn api.main:app --reload

test:
	uv run pytest

db-upgrade:
	uv run alembic upgrade head

db-downgrade:
	uv run alembic downgrade -1

db-revision:
	uv run alembic revision --autogenerate -m "$(name)"

db-seed:
	uv run python -m scripts.seed_cases

typecheck:
	uvx lefthook run pre-commit --command backend-typecheck --all-files

lint:
	uvx lefthook run pre-commit --command backend-lint --all-files

format:
	uvx lefthook run pre-commit --command backend-format --all-files
