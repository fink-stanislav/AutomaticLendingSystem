
import yaml
import os

from als.util import custom_config as cc

def read_config():
    filename = cc.get_keys_file()
    if filename[0] == '~':
        filename = os.path.expanduser(filename)
    with open(filename, 'r') as myfile:
        yml_data=myfile.read()

    keys_config = yaml.load(yml_data)
    return keys_config

global keys_config
keys_config = read_config()

def get_keys(name='polo'):
    global keys_config
    if keys_config.has_key(name):
        conf = keys_config[name]
        return {'api_key': conf['api_key'], 'secret': conf['secret']}
    else:
        return {}
