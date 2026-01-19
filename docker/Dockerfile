FROM python:3.10-slim AS base

ARG GID=1000
RUN groupadd -g $GID usergroup

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
# Add access to user via the user's group.
RUN usermod -aG usergroup appuser

# install poetry.
RUN python -m pip install --upgrade pip
RUN pip install poetry

RUN adduser git
# Setup git server filespace.
ARG REMOTEGIT=/remotegit
RUN mkdir $REMOTEGIT && chmod a+rwx $REMOTEGIT

# Make a local dir for the MIM tool, also /project is the mount point for
# the host projects which when mounted will hide the local MakeItMake.
RUN mkdir -p /projects/MakeItMineV2_5 && chmod -R a+wrx /projects

# Install git
RUN apt-get update && apt-get install -y git

# Add the docker group before installing docker which would create a default group.
ARG DOCKERGID # :python import grp; x=grp.getgrnam('docker').gr_gid:
RUN groupadd -g $DOCKERGID docker

# Install docker is quite the process:
RUN apt-get install -y ca-certificates curl gnupg
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg
RUN apt-get install -y lsb-release
# python slim is based on debian.
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list
RUN cat /etc/apt/sources.list.d/docker.list
RUN apt-get update
RUN apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

ARG LOCAL=/test_projects
RUN mkdir -p $LOCAL/testing && chown -R appuser:appgroup $LOCAL
RUN usermod -aG docker appuser

# Create a location for the remote repo for the testing project.
ARG REMOTE=$REMOTEGIT/testing
RUN mkdir $REMOTE && chmod a+rwx $REMOTE

# Create the local repo for the testing project.
COPY docker/artifacts $LOCAL/testing
RUN git config --global --add safe.directory $LOCAL/testing

FROM base AS projectbase

# Install MakeItMine as a local repo, this is also the mount point for the host
# version of the repo and while mounted it will hide the actual repo until
# the mount is lost.
COPY . /projects/MakeItMineV2_5
RUN chown -R appuser:appgroup /projects
RUN chown -R appuser:appgroup $LOCAL
RUN chown -R appuser:appgroup $REMOTE

FROM projectbase AS development

WORKDIR /projects/MakeItMineV2_5
USER appuser
# Config is written to ~/.config/pypoetry/config.toml
RUN poetry config virtualenvs.in-project true
# Using the default poetry configuration, the install occurs in poetry's cache
# found in .cache in users home directory.
RUN poetry install --with dev,inhouse_wsdev
WORKDIR $LOCAL/testing

FROM projectbase AS production

WORKDIR /projects/MakeItMineV2_5
USER appuser
# Config is written to ~/.config/pypoetry/config.toml
RUN poetry config virtualenvs.in-project true
# Install dependencies from local wheels and/or pypi/poetry cache, then
# use pip to install the wheel for the local project (called root by poetry).
RUN poetry install --with inhouse_wsprod --no-root
RUN pip install .download/*.whl
WORKDIR $LOCAL/testing
