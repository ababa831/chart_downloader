#!/bin/bash

poetry run python main.py $@
poetry run pip freeze > requirements.txt