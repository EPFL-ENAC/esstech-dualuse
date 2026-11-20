FROM python:3.13.6-bookworm
ENV UV_VERSION=0.9.13

# System dependencies
RUN apt update \
	&& apt install -y \
	libglew-dev \
	&& rm -rf /var/lib/apt/lists/*

RUN pip install "uv==$UV_VERSION"

WORKDIR /app

COPY uv.lock pyproject.toml /app/
COPY start.sh /app/
COPY api /app/api
COPY alembic.ini /app/alembic.ini
COPY migrations /app/migrations
COPY scripts /app/scripts

# Install exactly the versions in uv.lock, into the system Python so that
# start.sh finds alembic and uvicorn on PATH.
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --locked --no-cache

EXPOSE 8000

ENTRYPOINT ["sh", "start.sh"]
