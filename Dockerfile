# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Build stage.
FROM python:3.13.18-slim-trixie@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS builder

WORKDIR /code

# Dependencies for building google-re2.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        g++ \
        libabsl-dev \
        libgtest-dev \
        libbenchmark-dev \
        pybind11-dev \
        python3-pybind11 \
        python3-dev \
        libre2-dev && \
    rm -rf /var/lib/apt/lists/*

# See
# https://stackoverflow.com/a/48562835
RUN python -m venv /opt/venv
# Activate the venv
# See
# https://aleksac.me/blog/dont-use-pythondontwritebytecode-in-your-dockerfiles/
ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Copy production locked requirements file.
COPY ./linux-py3.13-requirements.lock /code/prod-constraints.txt

# Copy source code only.
COPY ./src/restmesh /code/restmesh

RUN pip install --require-hashes --no-deps --no-cache-dir --upgrade -r /code/prod-constraints.txt

#############
# Run stage #
#############
FROM python:3.13.18-slim-trixie@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90 AS runner

ENV PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Dependency to run google-re2.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libre2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code
RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid 10001 --shell /usr/sbin/nologin --create-home appuser

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder --chown=10001:10001 /code /code

USER 10001

CMD ["python", "-m", "restmesh.main", "--port", "8000", "--host", "0.0.0.0"]
