import logging.config
import yaml
from pythonjsonlogger import jsonlogger


def setup_logging(config_file):
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

setup_logging('config/logging.yml')
logger = logging.getLogger(__name__)
