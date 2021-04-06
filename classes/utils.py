import numpy as np, pandas as pd, json, os, datetime, time
import MetaTrader5 as mt5
from beeprint import pp #!pip install beeprint
import yaml
import msgpack


def dic_show(dic):
    pp(dic)

def load_config(filename):
    if filename[-4:] == '.yml': 
        return yaml_to_dic('configs/'+filename)
    elif filename[-5:] == '.json': 
        return json_to_dic('configs/'+filename)


# mt5 connect


def connect(demo=True):
    config = load_config('config.yml')
    if demo:
        login = config['mt5']['demo']['login']
        password = config['mt5']['demo']['password']
        server = config['mt5']['demo']['server']
    else:
        login = config['mt5']['live']['login']
        password = config['mt5']['live']['password']
        server = config['mt5']['live']['server']
    if not mt5.initialize(login=login, password=password,server=server):
        print("initialize() failed, error code =",mt5.last_error())


# msg pack

def msgpack_to_dic(path):
    with open(path, 'rb') as f:
        dic = msgpack.unpackb(f.read())
        f.close()
    return dic

def dic_to_msgpack(dic, path):
    with open(path, 'wb') as f:
        f.write(msgpack.packb(dic))
        f.close()

# json

def json_to_dic(path):
    with open(path, 'r') as f:
        dic = json.load(f)
        f.close()
    return dic

def dic_to_json(dic, path):
    with open(path, 'w') as f:
        json.load(dic)
        f.close()


# yaml

def yaml_to_dic(path):
    with open(path) as f:
        dic = yaml.load(f, Loader=yaml.FullLoader)
        f.close()
    return dic

def dic_to_json(dic, path):
    with open(path, 'w') as f:
        yaml.dump(dic)
        f.close()




