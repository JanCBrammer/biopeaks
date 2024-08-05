#!/bin/bash

./.devcontainer/install_system_dependencies.sh

curl -sSL https://install.python-poetry.org | python -
# Poetry creates its own virtual environment.
# To make sure Poetry doesn't redundantly nest a virtual environment
# within the Docker container we configure it as follows:
poetry config virtualenvs.create false --local
poetry install --with main,dev,build
