import yaml
import os

from src.custom_logging import logging_setup

current_dir = os.getcwd()

# Find the project root by traversing up the directory tree
while not os.path.isfile(os.path.join(current_dir, 'README.md')):
    # Change to the parent directory
    current_dir = os.path.dirname(current_dir)

project_root = current_dir

logging_setup()

with open(f'{project_root}/environment.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

API_CREDENTIALS = config.get('credentials')
