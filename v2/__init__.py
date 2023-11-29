import json
import yaml
import logging.config
import os
from pathlib import Path

current_dir = os.getcwd()

# Find the project root by traversing up the directory tree
while not os.path.isfile(os.path.join(current_dir, 'README.md')):
    # Change to the parent directory
    current_dir = os.path.dirname(current_dir)

project_root = current_dir

with open(Path(f"{project_root}/v2/log.json"), "r", encoding="UTF8") as f:
    logger_config = json.load(f)

logging.config.dictConfig(logger_config)

with open(f'{project_root}/environment.yaml', 'r') as stream:
    config = yaml.safe_load(stream)

API_CREDENTIALS = config.get('credentials')
