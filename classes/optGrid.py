import pandas as pd
import numpy as np
import json, os, time
import scipy.stats as stats
import datetime
from beeprint import pp
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from numba import njit
from multiprocessing import Pool
from trader import Trader
from tqdm import tqdm
from data import Datas




class GridOpt:
    def __init__(self, datas, prop_in_sample):
        self.datas = datas
        self.prop_in_sample = prop_in_sample

        self.best_params_val_ = None
        self.best_metrics_val_ = None  

    def predict(self, params_choices):
        # convert 1D dic in 2D dic of params, then apply params changes on datas.strategies and datas.transformers
        self.datas.edit_params(config_to_dic_params(params_choices)) 
        # recompile new datas (only transf & strategies)
        self.datas.compile(from_datasets=False)
        # create trader object and run backtesting
        trader = Trader(capital=1000, datas=get_in_sample_datas(self.datas, self.prop_in_sample))
        trader.backtest_noprint()
        # extract metrics
        metrics = trader.extract_metrics()[0]
        return list(metrics.values())[:-1] 


    def run(self, params_choices, optimizer):
        '''run the grid optimization
        optimize parameters on validation set by running a grid of backtest.
        '''
        list_config = self.get_cartesian_list_params_choices(params_choices)
        print(f'{datetime.datetime.now()} - running {len(list_config)} backtest')
        time.sleep(0.5)
        # create list of resutls
        list_results = np.zeros((len(list_config),15))
        for i in tqdm(range(len(list_config))):
            list_results[i] = self.predict(list_config[i])
        # extract best config
        print(f'{datetime.datetime.now()} - Selecting best config')
        best_config_index = optimizer.get_best_config_index(list_results)

        list_metrics_key = ['cumulative_pnl', 'avg_pnl_per_trades', 'daily_sharpe_ratio', 'profit_factor', 'accuracy_trades', 'proportion_sl', 'max_capital_drawdown', 'daily_return',  
                            'trades_per_day', 'cumulative_max_upnl', 'cumulative_min_upnl', 'avg_max_upnl_per_trade', 'avg_min_upnl_per_trade', 'avg_no_fee_pnl_per_trade', 'proportion_long']

        self.best_params_val_ = list_config[int(best_config_index)]
        self.best_metrics_val_ = {key:value for value,key in zip(list_results[int(best_config_index)], list_metrics_key)}

    def print_template_params(self):
        ''' print the params choices template with current params as list
        '''
        dic = {}
        for name,strategy in self.datas.strategies._dict.items():
            for key, value in strategy.params.items():
                dic[f'strategies/{name}/{key}'] =  [value]
        for name,transformer in self.datas.transformers._dict.items():
            for key, value in transformer.params.items():
                dic[f'transformers/{name}/{key}'] =  [value]
        pp(dic)

    def get_cartesian_list_params_choices(self, params_choices):
        '''
        params_choices is a dic of params list
        ex:
        params_choices = {
          'strategies/scalp/dephasage': [0.1, 0.5],
          'strategies/scalp/qty': [100, 200, 500],
          'transformers/atr/mult': [3],
          'transformers/atr/period': [14, 50],
          'transformers/floor/percent': [2],
          'transformers/floor/period': [50, 300],
          'transformers/trend/matype': [0],
          'transformers/trend/period': [200],
        }
        return a list of all possible outcomes with a cartesian product
        '''
        from sklearn.utils.extmath import cartesian
        cart_list = cartesian([v for v in params_choices.values()])
        return [{key:value for key,value in zip(params_choices.keys(), list_v)} for list_v in cart_list]

    def get_opt_df_trades(self):
        list_trades, trader = self.best_estimator_
        return pd.DataFrame(list_trades)

    def test_best_model(self):
        # convert 1D dic in 2D dic of params, then apply params changes on datas.strategies and datas.transformers
        self.datas.edit_params(config_to_dic_params(self.best_params_val_)) 
        # recompile new datas (only transf & strategies)
        self.datas.compile(from_datasets=False)
        # create trader object and run backtesting
        trader = Trader(capital=1000, datas=get_out_sample_datas(self.datas, self.prop_in_sample))
        trader.backtest_noprint()
        # extract metrics
        metrics = trader.extract_metrics()[0]

        #print(pp(trader.extract_metrics(preci='percent')))
        fig = trader.plot_standard_backtest_result()
        #fig.show(renderer="png", width=1200, height=600)
        fig.show()
        return metrics


def config_to_dic_params(config):
    ''' as input take something like 
    
    {'object/name/param_key_1': param_value_1, 
    ...}
    
    and return 
    {object: {
        name: {param1:value1, param2:value2, ...},
        ...
        },
    ...}
    '''
    dic = {}
    for k,v in config.items():
        field, name, key = k.split('/')
        if field not in dic:
            dic[field] = {}
        if name not in dic[field]:
            dic[field][name] = {}
        if key not in dic[field][name]:
            dic[field][name][key] = v
    return dic

def get_in_sample_datas(datas_obj, prop_val):
    d = Datas(datas_obj.config, datas_obj.start_year, datas_obj.start_month, datas_obj.end_year, datas_obj.end_month, False)
    index_last_insample = int(prop_val*len(datas_obj.arr_order_lists))
    d.tranformers = datas_obj.transformers
    d.strategies = datas_obj.strategies
    d.datasets = datas_obj.datasets
    d.arr_order_lists = datas_obj.arr_order_lists.copy()[:index_last_insample]
    d._arrs = {}
    for name in datas_obj._arrs:
        d._arrs[name] = {}
        for col in datas_obj._arrs[name]:
            d._arrs[name][col] = datas_obj._arrs[name][col].copy()[:index_last_insample]
    d._dfs = {}
    for name in datas_obj._dfs:
        d._dfs[name] = {}
        for col in datas_obj._dfs[name]:
            d._dfs[name][col] = datas_obj._dfs[name][col].copy()[:index_last_insample]
    return d

def get_out_sample_datas(datas_obj, prop_val):
    d = Datas(datas_obj.config, datas_obj.start_year, datas_obj.start_month, datas_obj.end_year, datas_obj.end_month, False)
    index_last_insample = int(prop_val*len(datas_obj.arr_order_lists))
    d.tranformers = datas_obj.transformers
    d.strategies = datas_obj.strategies
    d.datasets = datas_obj.datasets
    d.arr_order_lists = datas_obj.arr_order_lists.copy()[index_last_insample:]
    d._arrs = {}
    for name in datas_obj._arrs:
        d._arrs[name] = {}
        for col in datas_obj._arrs[name]:
            d._arrs[name][col] = datas_obj._arrs[name][col].copy()[index_last_insample:]
    d._dfs = {}
    for name in datas_obj._dfs:
        d._dfs[name] = {}
        for col in datas_obj._dfs[name]:
            d._dfs[name][col] = datas_obj._dfs[name][col].copy()[index_last_insample:]
    return d
