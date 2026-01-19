FROM python:3.10-slim AS base

RUN groupadd -r testgroup && useradd -m -r -g testgroup -s /bin/false testuser
RUN usermod -aG docker testuser
USER testuser
RUN mkdir /testing && chown testuser:testgroup /testing

FROM base AS development

WORKDIR /testing

FROM base AS production

WORKDIR /testing
