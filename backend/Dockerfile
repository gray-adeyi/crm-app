FROM docker.io/python:3.14-slim

ARG VERSION
ARG REVISION
ARG CREATED_AT
ARG USERNAME=josh
ARG USER_UID=1000
ARG USER_GID=1000

LABEL maintainer="StackCodeArtisan" \
      org.opencontainers.image.title="crm-app" \
      org.opencontainers.image.description="" \
      org.opencontainers.image.version=${VERSION} \
      org.opencontainers.image.authors="backend" \
      org.opencontainers.image.licenses="propeitary" \
      org.opencontainers.image.source="https://github.com/StackCodeArtisan/crm-app" \
      org.opencontainers.image.revision=${REVISION} \
      org.opencontainers.image.created=${CREATED_AT}

ENV PROJECT_DIR=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=${PROJECT_DIR} \
    # Place executables in the environment at the front of the path
    # Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
    PATH="/${PROJECT_DIR}/.venv/bin:$PATH" \
    # Compile bytecode
    # Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
    UV_COMPILE_BYTECODE=1 \
    # uv Cache
    # Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:0.11.8 /uv /uvx /bin/

WORKDIR ${PROJECT_DIR}


RUN apt-get update && apt-get install -y ca-certificates && \
    # Create the non-root user
    groupadd --gid ${USER_GID} ${USERNAME} \
      && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
      # Transfer project dir from root to non-root user \
      && chown -R ${USER_UID}:${USER_GID} ${PROJECT_DIR}

# Set non-root user
USER ${USERNAME}


# Install dependencies
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY --chown=${USER_UID}:${USER_GID} . .

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Expose port 8000 for service
EXPOSE 8000

ENTRYPOINT ["uv"]

# Command to run the application using Uvicorn
CMD ["run","fastapi","run","--app","app","--host", "0.0.0.0", "--port", "8000"]
