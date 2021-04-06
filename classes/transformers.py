'''
Object that store data transformation
add transformation with add function
Then the transformer will be set a a child of Datas
By runing Datas method apply_transformer it will create the custom arrays
'''



import numpy as np, pandas as pd, json, os, datetime, time, tulipy as ti, talib as ta


class Transformers():
    def __init__(self):
        self._dict = {}

    def add(self, name, function, params):
        self._dict[name] = Transformer(name, function, params)

    def __repr__(self):
        txt = ''
        for name,transformer in self._dict.items():
            txt += transformer.__repr__()
            txt += '\n'



class Transformer():
    def __init__(self, name, function, params):
        self.name = name
        self.function = function
        self.params = params

    def apply_on(self, dfs):
        return self.function(dfs, self.params)

    def __repr__(self):
        txt = f'Transformer "{self.name}"'
        for key, item in self.params.items():
            txt += f'\n  {key} = {item}'
        return txt