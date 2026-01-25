FROM python:3.10-slim AS base

RUN groupadd -r testgroup && useradd -m -r -g testgroup -s /bin/false testuser

RUN mkdir /testing && chown testuser:testgroup /testing

FROM base AS development

WORKDIR /testing
USER testuser

FROM base AS production

WORKDIR /testing
USER testuser
