
import yaml

from als.util import custom_config as cc

def read_config():
    filename = '{}/als/keys.yml'.format(cc.get_root_dir())

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
