import json, os, gzip
import datetime
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import bios


class DataManager():
    Crypto = 'Crypto'
    Stocks = 'Stocks'
    Forex = 'Forex'
    Forex_Major = 'Forex Major'
    CFDs = 'CFDs'
    Oil = 'Oil'
    Commodities = 'Commodities'
    Silver = 'Silver'
    Gold = 'Gold'

    def __init__(self, mod='Crypto'):


        self.path = f'D://Trading/Data/{mod}'

        dic_data = {}
        for broker in os.listdir(self.path):
            if '.json' not in broker:
                dic_data[broker] = {}
                for instrument in os.listdir(self.path+'/'+broker):
                    if '.json' not in instrument:
                        dic_data[broker][instrument] = {}
                        for symbol in os.listdir(self.path+'/'+broker+'/'+instrument):
                            dic_data[broker][instrument][symbol] = []
                            for timeframe in os.listdir(self.path+'/'+broker+'/'+instrument+'/'+symbol):
                                dic_data[broker][instrument][symbol].append(timeframe)
                                try:
                                    setattr(self, broker.upper()+'_'+instrument.upper()+'_'+symbol+'_'+timeframe, Dataset(mod, broker, instrument, symbol, timeframe))
                                except:
                                    pass


    def get_df(self, dataset, start_year, start_month, end_year, end_month, add_date=True):
        folder = f'D://Trading/Data/{dataset.field}/{dataset.broker}/{dataset.instrument}/{dataset.symbol}/{dataset.timeframe}/'

        def concat_successive(df1,df2):
            if len(df1) == 0:
                return df2
            elif len(df2) == 0:
                return df1
            else:
                end_time = df1.iloc[-1].time
                start_time = df2.iloc[0].time
                if end_time == start_time:
                    return pd.concat([df1.iloc[:-1],df2],axis=0).reset_index(drop=True)
                else:
                    return pd.concat([df1,df2],axis=0).reset_index(drop=True)

        def date_to_ymd_str(date):
            # return list of yyy, mm, dd as string (2 digit)
            return str(date).split(' ')[0].split('-')

        def date_next_month(date):
            year, month = date.year, date.month
            next_month = month % 12 + 1
            next_year = year + month // 12
            return datetime.datetime(next_year, next_month, date.day)

        df = pd.DataFrame()
        date = datetime.datetime(start_year, start_month, 1)
        end_date = datetime.datetime(end_year, end_month, 1)

        while date <= end_date:
            year_str = date_to_ymd_str(date)[0]
            month_str = date_to_ymd_str(date)[1]
            if year_str in os.listdir(folder):
                if f'{year_str}-{month_str}.csv.gz' in os.listdir(folder+year_str):
                    df = concat_successive(df,pd.read_csv(folder+f'{year_str}/{year_str}-{month_str}.csv.gz'))
            date = date_next_month(date)

        if add_date:
            df.loc[:,'date'] = pd.to_datetime(df.time, unit='s')

        return df




class Dataset(object):
    """docstring for Dataset"""
    def __init__(self,mod,  broker, instrument, symbol, timeframe):
        #super(Dataset, self).__init__()    
        self.field = mod
        self.broker = broker
        self.instrument = instrument
        self.symbol = symbol
        self.timeframe = timeframe
        self.path = f'D://Trading/Data/{self.field}/{self.broker}/{self.instrument}/{self.symbol}/{self.timeframe}/'
        with open(f'D://Trading/Data/{self.field}/{self.broker}.json', 'r') as f:
            dic_infos = json.load(f)
            f.close()
        if 'min' in timeframe:
            self.resampling_dict = dic_infos[instrument]['1min'][symbol]['resampling_dict']
            self.infos = dic_infos[instrument]['1min'][symbol]['infos']
        else:
            self.resampling_dict = dic_infos[instrument][timeframe][symbol]['resampling_dict']
            self.infos = dic_infos[instrument][timeframe][symbol]['infos']
        

    def __repr__(self):
        return f'Dataset of {self.field}:\n  Broker: {self.broker}\n  Instrument: {self.instrument}\n  Symbol: {self.symbol}\n  timeframe: {self.timeframe}\n  Path: {self.path}'


    def get_df(self, start_year, start_month, end_year, end_month, add_date=True):
        folder = self.path

        def concat_successive(df1,df2):
            if len(df1) == 0:
                return df2
            elif len(df2) == 0:
                return df1
            else:
                end_time = df1.iloc[-1].time
                start_time = df2.iloc[0].time
                if end_time == start_time:
                    return pd.concat([df1.iloc[:-1],df2],axis=0).reset_index(drop=True)
                else:
                    return pd.concat([df1,df2],axis=0).reset_index(drop=True)

        def date_to_ymd_str(date):
            # return list of yyy, mm, dd as string (2 digit)
            return str(date).split(' ')[0].split('-')

        def date_next_month(date):
            year, month = date.year, date.month
            next_month = month % 12 + 1
            next_year = year + month // 12
            return datetime.datetime(next_year, next_month, date.day)

        df = pd.DataFrame()
        date = datetime.datetime(start_year, start_month, 1)
        end_date = datetime.datetime(end_year, end_month, 1)

        while date <= end_date:
            year_str = date_to_ymd_str(date)[0]
            month_str = date_to_ymd_str(date)[1]
            if year_str in os.listdir(folder):
                if f'{year_str}-{month_str}.csv.gz' in os.listdir(folder+year_str):
                    df = concat_successive(df,pd.read_csv(folder+f'{year_str}/{year_str}-{month_str}.csv.gz'))
            date = date_next_month(date)

        if self.timeframe != '1min':
            df.loc[:,'date'] = pd.to_datetime(df.time, unit='s')
            df = df.set_index('date').resample(self.timeframe).agg(self.resampling_dict).reset_index(drop=True).drop_duplicates(subset=['time'])

        if add_date:
            df.loc[:,'date'] = pd.to_datetime(df.time, unit='s')

        return df

