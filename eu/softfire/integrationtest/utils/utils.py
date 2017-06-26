import configparser
import logging
import logging.config
import os

CONFIGURATION_FILE_PATH = "/etc/softfire/integration-test.ini"


def get_logger(name):
    logging.config.fileConfig(CONFIGURATION_FILE_PATH, disable_existing_loggers=False)
    return logging.getLogger(name)


log = get_logger(__name__)


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


def print_results(table):
    table = [['Test Phase', 'Result', 'Details']] + table
    col_width = [max(len(x) for x in col) for col in zip(*table)]
    line_range = range(0, len(table[0]))

    print("+ " + " + ".join('{:-<{}}'.format('', col_width[i]) for i in line_range) + " +")
    print("| " + " | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(table[0])) + " |")
    print("+ " + " + ".join('{:=<{}}'.format('', col_width[i]) for i in line_range) + " +")
    for i in range(1, len(table)):
        print("| " + " | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(table[i])) + " |")
        print("+ " + " + ".join('{:-<{}}'.format('', col_width[i]) for i in line_range) + " +")
