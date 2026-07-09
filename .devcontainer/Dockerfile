FROM mcr.microsoft.com/devcontainers/python:3.12-bookworm

ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Basic tools useful for Django, npm, and network debugging.
RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        git \
        iputils-ping \
        netcat-openbsd \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*