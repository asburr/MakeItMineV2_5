FROM python:3.10-slim AS base

# install poetry.
RUN pip install poetry
RUN poetry config virtualenvs.create false

RUN adduser git
# Setup git server filespace.
ARG REMOTEGIT=/remotegit
RUN mkdir $REMOTEGIT && chmod a+rwx $REMOTEGIT
# Create a "remote" repo for MakeItMine.
ARG MIMREMOTE=$REMOTEGIT/MakeItMine
RUN mkdir $MIMREMOTE && chmod a+rwx $MIMREMOTE

# Install git
RUN apt-get update && apt-get install -y git

# Processes in a Linux-based container run as root.
# Running containers as root is generally discouraged as a best practice for
# production environments due to potential security vulnerabilities. If a
# container is compromised, the attacker may have elevated privileges on the
# host system.
# The USER instruction is used to set the user for all subsequent RUN, CMD,
# and ENTRYPOINT instructions.
# -r creates a system account (or system user) to run the application with
# limited privileges, improving security by restricting damage if compromised.
# These accounts have no password, a disabled login shell.
# -m creates a home directory needed for poetry's cache.
RUN groupadd -r appgroup && useradd -m -r -g appgroup -s /bin/false appuser
USER appuser

FROM base AS projectbase

# Make a new local repo from the MakeItMine repo - remove the .git directory.
COPY --chown=appuser:appgroup . /MakeItMine
RUN rm -rf /MakeItMine/.git
WORKDIR /MakeItMine

# By default in a Unix-like environment (including containers),
# Poetry creates its cache and virtual environments within the user's
# home directory.
# The following install of the dependencies occurs in poetry's cache at users
# home.
RUN poetry install --no-root --without dev,wsdev,wsprod

FROM projectbase AS development

# Install development dependencies. Also, Install workspace dependencies as
# editable packages and editable for the local project.
RUN --mount=type=bind,from=projects,source=.,target=/projects \
  cd /projects/MakeItMineV2_5 && \
  poetry install --with dev,wsdev
WORKDIR /projects/MakeItMineV2_5

FROM projectbase AS production

# Install dependencies local wheels as production packages, but editable still
# for the local project.
RUN poetry install --with wsprod