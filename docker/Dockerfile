FROM python:3.10-slim AS base

ARG GID=1000
RUN groupadd -g $GID usergroup

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

# note: Why copy the whole project?
# Copying just the build dependencies to quicken the build time only works
# when the cache is not pruned, MIM prunes the caches after each build.
# Instead we tell MIM to detect a newer lockfile to trigger a docker rebuild.
# MIM: rebuild_target: dkbuild = poetry.lock
## COPY pyproject.toml poetry.lock ./
## RUN poetry install --with dev,inhouse_wsdev
COPY . /projects/MakeItMineV2_5

# Note: Why create a user?
# Processes in a Linux-based container run as root. Running containers as
# root is generally discouraged as a best practice for production
# environments due to potential security vulnerabilities. If a container is
# compromised, the attacker may have elevated privileges on the host system.
# The USER instruction is used to set the user for all subsequent RUN, CMD,
# and ENTRYPOINT instructions.
# useradd options -r creates a system account (or system user) to run the
# application with limited privileges, improving security by restricting
# damage if compromised. These accounts have no password, a disabled login
# shell. -m creates a home directory needed for poetry's cache.

FROM projectbase AS development

WORKDIR /projects/MakeItMineV2_5
# Note: Why GID and UID in development?
# appuser and appgroup is created using the UID and GID of the host's user this
# is to allow the container the same permissions as the host when accessing
# the mounted repo.
ARG UID
ARG GID
RUN groupadd -u $GID -r appgroup && useradd -u $UID -m -r -g appgroup -s /bin/false appuser
RUN usermod -aG docker appuser
RUN mkdir -p $LOCAL/testing && chown -R appuser:appgroup $LOCAL
RUN chown -R appuser:appgroup /projects
RUN chown -R appuser:appgroup $LOCAL
RUN chown -R appuser:appgroup $REMOTE
USER appuser
# Note: where is the venv?
# Using the default poetry configuration, the install occurs in the venv
# located in poetry's cache found in the appuser home directory.
# Note: How does the mounted repo work?
# The workspace, $HOME/projects/, is mounted to /projects. and this hides the
# containers copy of the repo, but the venv is in the appuser home directory
# which is uneffected by the mount and will retain the following install
# and editable install.
# Note: when container needs rebuilding?
# When the dependencies change in the host repo, the container will retain
# the prior dependencies from the last docker build. A rebuild is needed to
# update the dependencies within the container.
RUN poetry install --with dev,inhouse_wsdev
WORKDIR $LOCAL/testing

FROM projectbase AS production

WORKDIR /projects/MakeItMineV2_5

# Note: Why 1001 and 1001 in production?
# The UID and GID are fixed within the production repo for any external mounts
# with persistent files that need to be accessible by the same UID/GID between
# container runs.
RUN groupadd -r appgroup && useradd -m -r -g appgroup -s /bin/false appuser
RUN usermod -aG docker appuser
RUN mkdir -p $LOCAL/testing && chown -R appuser:appgroup $LOCAL
RUN chown -R appuser:appgroup /projects
RUN chown -R appuser:appgroup $LOCAL
RUN chown -R appuser:appgroup $REMOTE
USER appuser
# Install dependencies from local wheels and/or pypi/poetry cache, then
# use pip to install the wheel for the local project (called root by poetry).
RUN poetry install --with inhouse_wsprod --no-root
RUN pip install .download/*.whl
WORKDIR $LOCAL/testing
