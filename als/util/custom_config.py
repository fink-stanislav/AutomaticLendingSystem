
"""
Module for reading application configuration. Provides helper methods for easy access to configuration keys.
"""

import yaml
import pkg_resources

global_app_config = {}

def get_config_value(name):
    global global_app_config
    return global_app_config[name]

def set_config_value(name, value):
    global global_app_config
    global_app_config[name] = value

def get_test():
    return get_config_value('test')

def get_root_dir():
    return get_config_value('root_dir')

def get_keys_file():
    return get_config_value('keys_file')

class ConfigurationIsIncorrectException(Exception):
    def __init__(self, message):
        super(ConfigurationIsIncorrectException, self).__init__()
        self.message = message

def init_config(package_name='als', config_file_name='app_config', config_name='als'):
    filename = '{}.yml'.format(config_file_name)
    filename = pkg_resources.resource_filename(package_name, filename)

    with open(filename, 'r') as myfile:
        yml_data=myfile.read()

    global global_app_config
    global_app_config = yaml.load(yml_data)
    global_app_config = global_app_config[config_name]

init_config()
