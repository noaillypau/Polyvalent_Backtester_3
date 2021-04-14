import numpy as np 
import pandas as pd 

class Metric:
    cumulative_pnl = 0
    avg_pnl_per_trades = 1
    daily_sharpe_ratio = 2
    profit_factor = 3
    accuracy_trades = 4
    proportion_sl = 5
    max_capital_drawdown = 6
    daily_return = 7
    trades_per_day = 8
    cumulative_max_upnl = 9
    cumulative_min_upnl = 10
    avg_max_upnl_per_trade = 11
    avg_min_upnl_per_trade = 12
    avg_no_fee_pnl_per_trade = 13
    proportion_long = 14


class OptimizerSharpeRatio():
    '''
    max_metrics is a dic of 'metric_key': max_value
    This will only take results that yielded a metric 'metric_key' higher than max_value
    '''
    def __init__(self, min_metrics={}, max_metrics={}):
        self._dict = {
            'id': 'sharpeRatio',
            'min_metrics': min_metrics,
            'max_metrics': max_metrics
        }

    def get_best_config_index(self, matrix):
        '''matrix is the n*p matrix obtained with max results
        '''
        matrix = np.append(matrix, [[i] for i in range(0,len(matrix))], axis=1)
        # filter value
        for index,value in self._dict['max_metrics'].items():
            if len(matrix)>0:
                matrix = matrix[matrix[:,index]<=value]
        for index,value in self._dict['min_metrics'].items():
            if len(matrix)>0:
                matrix = matrix[matrix[:,index]>=value]
        #
        if len(matrix)>0:
            max_index = np.argmax(matrix[:,Metric.daily_sharpe_ratio])
            return matrix[max_index][-1]

        else:
            return None
