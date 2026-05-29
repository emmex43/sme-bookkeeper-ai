#!/usr/bin/env bash
# exit on error
set -o errexit

# Install all the python packages
pip install -r requirements.txt

# Gather all the Tailwind CSS files
python manage.py collectstatic --no-input

# Set up the live database
python manage.py migrate