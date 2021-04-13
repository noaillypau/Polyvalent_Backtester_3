import numpy as np, pandas as pd, json, os, datetime, time
import talib as ta
import MetaTrader5 as mt5
from dataManager import Dataset
from tqdm import tqdm
import inspect

class Datas():
    def __init__(self, config, start_year, start_month, end_year, end_month, debug=True):
        self.datasets = Datasets()
        self.config = config
        self.debug = debug
        self._arrs = {}
        self._dfs = {}

        self.start_year, self.start_month, self.end_year, self.end_month = start_year, start_month, end_year, end_month



    def log(self, msg):
        if self.debug:
            print(f'[{datetime.datetime.now()}] - {msg}')

    def add_dataset(self, name, dataset):
        self.datasets.add(name, dataset)

    def set_transformers(self, transformers):
        self.transformers = transformers

    def set_strategies(self, strategies):
        self.strategies = strategies

    def compile(self, from_datasets=True):
        if from_datasets:
            self.compile_datasets()

        self.compile_transformers()

        self.compile_strategies()

    def compile_datasets(self):
        print(f'\n[{datetime.datetime.now()}] - Starting datasets compilation...')
        nbs_datasets = 0
        for name, dataset in self.datasets._dict.items():
            self.log(f'Adding dataset {name}')
            self._dfs[name] = dataset.get_df(self.start_year, self.start_month, self.end_year, self.end_month, add_date=True).ffill()
            nbs_datasets += 1
        print(f'[{datetime.datetime.now()}] - {nbs_datasets} datasets have been compiled.')

    def compile_transformers(self):
        print(f'\n[{datetime.datetime.now()}] - Starting transformers compilation...')
        nbs_transformers = 0
        for name, transformer in self.transformers._dict.items():
            self._dfs = transformer.apply_on(self._dfs)
            nbs_transformers += 1
        self.create_arrs()
        print(f'[{datetime.datetime.now()}] - {nbs_transformers} transformers have been compiled.')

    def create_arrs(self):
        for symbol in self._dfs:
            self._arrs[symbol] = {col:self._dfs[symbol][col].to_numpy() for col in self._dfs[symbol].columns}

    def compile_strategies(self):
        list_symbol = [key for key in self.strategies.get_dic_symbol_strategy()]

        print(f'\n[{datetime.datetime.now()}] - Starting strategies compilation...')
        time.sleep(0.5)



        arr_order_lists = np.empty(len(self._arrs[list_symbol[0]]['time']), dtype=object)
        for i in tqdm(range(len(arr_order_lists))):
            arr_order_lists[i] = self.strategies.compute(self._arrs, i)
            
            
        print(f'[{datetime.datetime.now()}] - {len(self.strategies._dict)} strategies have been compiled.')

        self.arr_order_lists = arr_order_lists


    def get_source_dict(self):
        dic = {
            "start_year": self.start_year,
            "start_month": self.start_month,
            "end_year": self.end_year,
            "end_month": self.end_month,
            "datasets": {
                
            },
            "transformers": {
                
            },
            "strategies":{
                
            }
        }

        # transformers
        for name,dataset in self.datasets._dict.items():
            dic['datasets'][name] = {
                "path": dataset.path,
                "infos": dataset.infos
            }

        # transformers
        for name,transformer in self.transformers._dict.items():
            dic['transformers'][name] = {
                "name": name,
                "function_str": inspect.getsource(transformer.function),
                "params": transformer.params
            }


        # strategies
        for name,strategy in self.strategies._dict.items():
            dic['strategies'][name] = {
                "name": name,
                "trigger_str": inspect.getsource(strategy.trigger),
                "params": strategy.params,
                "symbol": strategy.symbol
            }

        return dic








class Datasets(object):
    """docstring for Datasets"""
    def __init__(self):
        #super(Datasets, self).__init__()
        self._dict = {}
    
    def add(self, name, dataset):
        self._dict[name] = dataset
        setattr(self, name, dataset)

    def __repr__(self):
        txt = ''
        for name,item in self._dict.items():
            txt += '\n'+name+'\n'
            txt += item.__repr__()
            txt += '\n'
        return txt

    def apply():
        pass
