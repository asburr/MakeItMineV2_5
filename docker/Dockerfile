FROM python:3.10-slim AS base

# install poetry.
RUN pip install poetry
RUN poetry config virtualenvs.create false

RUN adduser git
# Setup git server filespace.
ARG REMOTEGIT=/remotegit
RUN mkdir $REMOTEGIT && chmod a+rwx $REMOTEGIT

# make dir for the MIM tool.
RUN mkdir -p /projects/MakeItMineV2_5 && chmod -R a+wrx /projects/MakeItMineV2_5

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
RUN usermod -aG docker appuser
USER appuser

# Create a "remote" repo for MakeItMine.
ARG MIMREMOTE=$REMOTEGIT/MakeItMine
RUN mkdir $MIMREMOTE && chmod a+rwx $MIMREMOTE

FROM base AS projectbase

# Make a new local repo from the MakeItMine repo - remove the .git directory.
COPY --chown=appuser:appgroup . /MakeItMine
RUN rm -rf /MakeItMine/.git

# Now create the actual repo which is mounted over in devlopment.
# Make a new local repo from the MakeItMine repo - remove the .git directory.
# By default in a Unix-like environment (including containers),
# Poetry creates its cache and virtual environments within the user's
# home directory.
COPY --chown=appuser:appgroup . /projects/MakeItMineV2_5
RUN git config --global --add safe.directory /projects/MakeItMineV2_5

FROM projectbase AS development

# The following install of the dependencies occurs in poetry's cache at users
# home.
WORKDIR /projects/MakeItMineV2_5
RUN poetry install --with wsdev
WORKDIR /MakeItMine

FROM projectbase AS production

# Install dependencies local wheels as production packages, but editable still
# for the local project.
WORKDIR /projects/MakeItMineV2_5
RUN poetry install --with wsprod
WORKDIR /MakeItMine