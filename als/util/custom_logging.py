
"""
Module provides basic logging functionality. Loggers are split between traders and agents to make logs distinguishable
"""

import yaml
import logging.config
import pkg_resources

def init_config(package_name='als', config_file_name='logging_config'):
    filename = '{}.yml'.format(config_file_name)
    filename = pkg_resources.resource_filename(package_name, filename)

    with open(filename, 'r') as myfile:
        yml_data=myfile.read()

    logging_config = yaml.load(yml_data)
    logging.config.dictConfig(logging_config['logging'])

init_config()

def get_logger(name):
    return logging.getLogger(name)
