# docker (dk) make

## Dockerfile structure

```
FROM <base image> AS base

# install on top of the base image

FROM base AS development

# Install development on top of the base

FROM base AS production

# Install production on top of the base
```

## Automatic ARG
MIM supports running code on the host to set ARG. The example shows DOCKERGID
set to the users group id.
```
ARG DOCKERGID # :python import grp; x=grp.getgrnam('docker').gr_gid:
```