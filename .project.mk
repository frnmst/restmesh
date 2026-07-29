# Copyright (C) 2024-2026 Franco Masotti (see /README.md)
# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Change these two. Required.
PROJECT_NAME := python-makefile
PYTHON_MODULE_NAME := python_makefile

# Required.
MAKEFILE_SOURCE := https://repos.franco.net.eu.org/frnmst/python-makefile/raw/branch/master/Makefile.linux.example
DOCKER_BUILD_PYTHON_DIST_SOURCE := https://repos.franco.net.eu.org/frnmst/python-makefile/raw/branch/master/Dockerfile.python3.13_hatchling.build.example

bootstrap:
	curl -o Makefile $(MAKEFILE_SOURCE)
	curl -o Dockerfile.python3.13_hatchling.build $(DOCKER_BUILD_PYTHON_DIST_SOURCE)

# Add extra targets here. Optional.
pytest:
	$(VENV_ACTIVATE) \
		&& pytest; \
		$(VENV_DEACTIVATE)

tox:
	$(VENV_ACTIVATE) \
		&& tox; \
		$(VENV_DEACTIVATE)

serve-dev:
	$(VENV_ACTIVATE) \
		&& fastapi dev; \
		$(VENV_DEACTIVATE)

# See
# https://fastapi.tiangolo.com/deployment/manually/
serve-prod:
	$(VENV_ACTIVATE) \
		&& fastapi run; \
		$(VENV_DEACTIVATE)

serve-prod-global:
	$(VENV_ACTIVATE) \
		&& restmesh --host 0.0.0.0 --port 8000; \
		$(VENV_DEACTIVATE)
