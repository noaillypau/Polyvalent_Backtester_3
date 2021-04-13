import json, os, gzip
import datetime
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import bios


class Dataset(object):
    """docstring for Dataset"""
    def __init__(self, path, maker_fee=-0.00025, taker_fee=0.00075, contract_value_in_usd=1):
        self.path = path
        self.infos = {
            "maker_fee":maker_fee,
            "taker_fee": taker_fee,
            "contract_value_in_usd":contract_value_in_usd
        }
        

    def __repr__(self):
        return f'infos: {self.infos}\n  Path: {self.path}'


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
            date_str = date.strftime('%Y-%m')
            if f'{date_str}.pkl' in os.listdir(folder):
                df = concat_successive(df,pd.read_pickle(folder+f'{date_str}.pkl'))
            date = date_next_month(date)

        if add_date:
            df.loc[:,'date'] = pd.to_datetime(df.time, unit='s')

        return df
