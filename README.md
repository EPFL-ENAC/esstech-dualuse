# EssentialTech Dual-Use

## Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, SQLModel, Alembic, PostgreSQL |
| Frontend | Node.js, Quasar v2, Vue 3, Pinia, Vue Router, vue-i18n, TypeScript |
| Tooling | uv, npm, Lefthook, Commitlint, Ruff, ty, ESLint, Prettier |
| CI/CD | GitHub Actions (checks, tests, deploy) |
| Containers | Docker, docker-compose (PostgreSQL) |

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) Python package and project manager
- [npm](https://docs.npmjs.com/) Node.js package manager
- [Docker](https://docs.docker.com/) with Docker Compose
- Make

## Deploying locally

Clone the repository:

```bash
git clone https://github.com/EPFL-ENAC/esstech-dualuse.git
cd esstech-dualuse
```

Setup your environment by running:

```bash
make install
```

This step installs the backend and frontend dependencies and creates a local `.env`
file from `.env.example` if none exists.

### Backend

In one shell, run:

```bash
make run-db
make run-backend
```

The interactive API documentation will be available at
[http://localhost:8000/docs](http://localhost:8000/docs).

The health check endpoint is at [http://localhost:8000/healthz](http://localhost:8000/healthz).

### Frontend

In another shell, run:

```bash
make run-frontend
```

The website will be available at [http://localhost:9000](http://localhost:9000).

## Database migrations

The backend uses [Alembic](https://alembic.sqlalchemy.org/) for schema migrations.
Manage them through the `backend/Makefile` (forwarded from the root `Makefile`):

```bash
# Apply all pending migrations to the database (start `make run-db` first)
make db-upgrade

# Roll back the last migration
make db-downgrade

# Autogenerate a migration revision from your SQLModel model changes
make db-revision name="describe the change"
```

The `name` argument in `db-revision` is required and becomes the migration message.

## Standalone package (backend/package)

The `backend/package/` directory is a standalone Python package (`dualuse`). It is:

- a **uv workspace member** of the `backend/` project (`[tool.uv.workspace]`), and
- installed as a regular **dependency** of the backend via `[tool.uv.sources]`,
  so the FastAPI app can `import dualuse` directly.

This keeps the package independently editable and testable while linking it into the
backend at install time (locally and in the Docker image, where it is copied and resolved
from the workspace).

The package has its own tooling under `backend/package/`:

```bash
cd backend/package
make install   # create a uv venv and install with dev dependencies
make test      # run pytest
make lint      # run ruff
make format    # run ruff format
```

### Install backend/package from git

Because it is a normal distributable Python package, you can also install `backend/package`
directly from the repository, without cloning it first:

```bash
pip install "git+https://github.com/EPFL-ENAC/esstech-dualuse.git#subdirectory=backend/package"
```

You can also pin a specific branch or tag for reproducible installs:

```bash
pip install "git+https://github.com/EPFL-ENAC/esstech-dualuse.git@main#subdirectory=backend/package"
```

To use the package inside another project, add the git URL above to that project's
dependencies, for example in `requirements.txt` or in `pyproject.toml`.

## Development

### Backend

The backend is a FastAPI application under `backend/api/`. The project layout is:

| Path | Purpose |
| --- | --- |
| `backend/api/main.py` | Application and router registration |
| `backend/api/config.py` | Pydantic settings loaded from `.env` |
| `backend/api/db.py` | Async engine and session helpers |
| `backend/api/models/` | SQLModel table models |
| `backend/api/services/` | Business logic |
| `backend/api/views/` | FastAPI routers (endpoints) |
| `backend/migrations/` | Alembic migration scripts |
| `backend/tests/` | pytest test suite |

To run backend checks:

```bash
cd backend
make test      # run pytest
make lint      # run ruff
make format    # run ruff format
make typecheck # run ty
```

### Frontend

The frontend is a Quasar v2 SPA under `frontend/src/`. The project layout is:

| Path | Purpose |
| --- | --- |
| `frontend/src/router/` | Vue Router routes |
| `frontend/src/layouts/` | Page layouts |
| `frontend/src/pages/` | Page components |
| `frontend/src/components/` | Reusable components |
| `frontend/src/stores/` | Pinia stores |
| `frontend/src/boot/` | Quasar boot files |
| `frontend/src/i18n/` | vue-i18n locale messages |

To run frontend checks:

```bash
cd frontend
npm run lint      # run eslint
npm run format    # run prettier
npm run typecheck # run vue-tsc
```

### LLM

The backend includes a minimal example for using the OpenAI library. Configuration
lives in `api/config.py` (and `.env`):

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENAI_API_URL` | `https://inference-rcp.epfl.ch/v1` | Base URL of the OpenAI-compatible API (EPFL inference) |
| `OPENAI_API_KEY` | (none) | API key. **Required**; must be set in `.env` (see below). |
| `MODEL_NAME` | `deepseek-ai/DeepSeek-V4-Flash-0731` | Model used for completions |

The `OPENAI_API_KEY` is **required and has no default value**. You must set it in your
local `.env` file (created from `.env.example` by `make install`):

```bash
# .env
OPENAI_API_KEY=your-real-key-here
```

Without it, the application fails to start with a settings validation error.

The `complete()` helper in `api/llm.py` sends a prompt and returns the text answer:

```python
from api.llm import complete

answer = await complete('Explain this project in one sentence.')
```

The shared `AsyncOpenAI` client is created lazily by `get_openai_client()`. It raises a
clear error if you call it without a configured key.

### Pre-commit hooks

This project uses [Lefthook](https://lefthook.dev/) for pre-commit and commit-msg hooks
(typecheck, lint, format, codespell, and commitlint). They run automatically on commit.

You can run all hooks manually without committing:

```bash
make lint
```

Commit messages must follow the
[Conventional Commits](https://www.conventionalcommits.org/) convention.

## CI/CD

GitHub Actions run on every push and pull request:

- `.github/workflows/checks.yml`: lint and typecheck for backend and frontend.
- `.github/workflows/tests.yml`: run the backend test suite.
- `.github/workflows/deploy.yml`: build, push, and deploy on `dev`/`stage` pushes and
  version tags. The target org/repo must be set in the workflow inputs before use.

## License

All rights reserved.
