FROM python:3.13-slim-bookworm

RUN set -x && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

ENV UV_PYTHON_DOWNLOADS=0
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=from=ghcr.io/astral-sh/uv:python3.13-bookworm-slim,source=/usr/local/bin/uv,target=/bin/uv \
    uv sync --locked --no-install-project --no-editable

COPY . ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=from=ghcr.io/astral-sh/uv:python3.13-bookworm-slim,source=/usr/local/bin/uv,target=/bin/uv \
    uv sync --locked --no-editable

ARG user=fastapi
ARG group=fastapi
ARG uid=10000
ARG gid=10001

RUN groupadd -g ${gid} ${group} \
    && useradd -l -u ${uid} -g ${gid} -m -s /bin/bash ${user}

USER ${user}

ENV PATH="/src/.venv/bin:$PATH"

ENTRYPOINT ["fastapi"]
CMD ["run"]