import numpy as np, pandas as pd, json, os, datetime, time

class Signal():
    def __init__(self, datas, tids):
        self.datas = datas
        self.tids = tids

    def compute_entries(self):
        
        self.list_entry_signals = []

    def compute_exit(self):
        
        self.list_exit_signals = []

    def debug(self, i):
        for tid,item in self.tids.dict.items():
            print('\ntid={}  symbol={}  index={}'.format(tid, item['symbol'], i))
            print(item['isEntry_func'](self.datas, i))
            print(item['isExit_func'](self.datas, i))