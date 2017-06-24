import configparser
import os

import logging
import logging.config

log = logging.getLogger(__name__)

CONFIGURATION_FILE_PATH = "/etc/softfire/integration-test.ini"



def get_logger(name):
    logging.config.fileConfig(CONFIGURATION_FILE_PATH)
    return logging.getLogger(name)


def get_config_parser():
    """
    Get the ConfigParser object containing the system configurations

    :return: ConfigParser object containing the system configurations
    """
    config = configparser.ConfigParser()
    if os.path.exists(CONFIGURATION_FILE_PATH) and os.path.isfile(CONFIGURATION_FILE_PATH):
        config.read(CONFIGURATION_FILE_PATH)
        return config
    else:
        logging.error("Config file not found, create %s" % CONFIGURATION_FILE_PATH)
        exit(1)

def get_config_value(section, key, default=None):
    config = get_config_parser()
    if default is None:
        return config.get(section=section, option=key)
    try:
        return config.get(section=section, option=key)
    except configparser.NoOptionError:
        return default
    except configparser.NoSectionError:
        return default