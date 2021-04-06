import numpy as np, pandas as pd, json, os, datetime, time
from order import Order

class Strategies():
    def __init__(self):
        self._dict = {}

    def add(self, name, strategy):
        self._dict[name] = strategy

    def compute(self, arrs, index):
        list_order = []
        for name,strategy in self._dict.items():
            list_order = list_order + strategy.compute(arrs, index)
        return list_order

    def get_dic_symbol_strategy(self):
        dic_strategy = {}
        for name,strategy in self._dict.items():
            if strategy.symbol not in dic_strategy:
                dic_strategy[strategy.symbol] = []
            dic_strategy[strategy.symbol].append(strategy)
        return dic_strategy

    def __repr__(self):
        txt = f'Strategies:\n'
        for key, item in self._dict.items():
            txt += f'\nName: {key}\n{item}\n'
        return txt



'''
Strategy object

create a strategy object with :
    dataset_name: can be string or list string, set on whioch asset the order will be passed
    trigger: function of dic of numpys (datas._dic) and index: will determine wether to send orders or not depending on index
    list_order: list of orders to be sent
'''

class Strategy():
    def __init__(self, trigger, symbol, params):
        self.trigger = trigger
        self.params = params
        self.symbol = symbol

    def compute(self, arrs, index):
        return self.trigger(arrs, self.params, self.symbol, index)

    def __repr__(self):
        txt = f'Strategy on {self.symbol} with params:'
        for key, item in self.params.items():
            txt += f'\n  {key}: {item}'
        return txt




