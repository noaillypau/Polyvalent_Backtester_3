import numpy as np, pandas as pd, json, os, datetime, time
from tqdm import tqdm
from beeprint import pp #!pip install beeprint
from csv import DictWriter
from utils import dic_to_msgpack, msgpack_to_dic

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from colormap import rgb2hex  


class Trader():
    def __init__(self, capital, datas):
        self.init_capital = capital
        self.capital = capital

        self.pending_orders = {}
        self.positions = {}

        self.list_trades = []
        self.nbs_trades = 0
        self.current_pnl = 0
        
        self.datas = datas
        
    def get_dataset_info(self, symbol, key=None):
        if key == None:
            return self.datas.datasets._dict[symbol].infos
        return self.datas.datasets._dict[symbol].infos[key]
        
    def get_taker_fee(self, symbol):
        return self.datas.datasets._dict[symbol].infos['taker_fee']
    
    def get_maker_fee(self, symbol):
        return self.datas.datasets._dict[symbol].infos['maker_fee']
    
    def get_qty_to_usd(self, symbol, qty=1):
        return self.datas.datasets._dict[symbol].infos['contract_value_in_usd'] * qty
    
    def get_arr_value(self, symbol, col, index):
        return self.datas._arrs[symbol][col][index]
    
    def entry_market(self, order, index):
        symbol = order.symbol
        id_position = order.id
        qty = order.qty
        sl = order.sl
        tp = order.tp       
        
        position = {
            'symbol': symbol,
            'id': order.id,
            'entry_index': index,
            'entry_time': self.get_arr_value(symbol, 'time', index),
            'entry_price': {1:self.get_arr_value(symbol, 'ask_close', index), -1:self.get_arr_value(symbol, 'bid_close', index)}[order.direction],
            'entry_fill_iteration': 0,
            'entry_fill_delay_sec': 0,
            'direction': order.direction,
            'entry_fee': self.get_taker_fee(symbol),
            'entry_type': 'market',
            'qty': qty,
            'qty_in_usd': self.get_qty_to_usd(symbol, qty=qty),
            "max_upnl": 0,
            "min_upnl": 0,
            'editable': order.editable_position
        }
        
        if tp != None:
            position['tp'] = tp
        if sl != None:
            position['sl'] = sl
        
        self.capital -= position['qty_in_usd']
        self.positions[id_position] = position.copy()        
    
    def exit_market(self, id_position, index):
        position = self.positions[id_position]
        symbol = position['symbol']
        dic_trades = position.copy()
        dic_trades['exit_index'] = index
        dic_trades['exit_time'] = self.get_arr_value(symbol, 'time', index)
        dic_trades['exit_type'] = 'market'
        dic_trades['exit_fill_iteration'] = 0
        dic_trades['exit_fill_delay_sec'] = 0
        if dic_trades['direction'] == 1:
            dic_trades['exit_price'] = self.get_arr_value(symbol, 'bid_close', index)
        else:
            dic_trades['exit_price'] = self.get_arr_value(symbol, 'ask_close', index)
        dic_trades['exit_fee'] = self.get_taker_fee(symbol)
        dic_trades['total_fee'] = dic_trades['exit_fee'] + dic_trades['entry_fee']
        dic_trades['pnl_no_fee'] = position['direction'] * (dic_trades['exit_price'] - dic_trades['entry_price'])/ dic_trades['entry_price']
        dic_trades['pnl'] = dic_trades['pnl_no_fee'] - dic_trades['total_fee']
        dic_trades['pnl_usd'] = dic_trades['pnl'] * dic_trades['qty_in_usd']
        self.capital = self.capital + dic_trades['pnl_usd']
        dic_trades['capital'] = self.capital
        
        self.list_trades.append(dic_trades)
        self.nbs_trades += 1
        self.current_pnl += dic_trades['pnl']
        del self.positions[id_position]
        
    def post_pending_order(self, order, index):     
        id_position = order.id
        symbol = order.symbol
        qty = order.qty
        sl = order.sl
        tp = order.tp   
        
        pending_order = {
            'symbol': symbol,
            'id': order.id,
            'posted_index': index,
            'posted_time': self.get_arr_value(symbol, 'time', index),
            'price': order.price,
            'direction': order.direction,
            'qty': qty,
            'qty_in_usd': self.get_qty_to_usd(symbol, qty=qty),
            'editable_pending': order.editable_pending,
            'editable_position': order.editable_position
        }
        
        if tp != None:
            pending_order['tp'] = tp
        if sl != None:
            pending_order['sl'] = sl        
        
        self.capital -= pending_order['qty_in_usd']
        self.pending_orders[id_position] = pending_order.copy()
        
        
    def edit_pending_order(self, order, index):       
        if self.pending_orders[order.id]['editable_pending']:
            
            self.pending_orders[order.id]['price'] = order.price
            
            if order.tp != None:
                self.pending_orders[order.id]['tp'] = order.tp
            if order.sl != None:
                self.pending_orders[order.id]['sl'] = order.sl 
        
    def edit_position(self, order, index):        
        if self.positions[order.id]['editable']:
            
            if order.tp != None:
                self.positions[order.id]['tp'] = order.tp
            if order.sl != None:
                self.positions[order.id]['sl'] = order.sl 
        
    
    def compute_order(self, order, index):
        if order.mode == 0: # entry order
            if order.type == 0: # entry market
                if order.id not in self.positions:
                    self.entry_market(order, index)
                
            elif order.type == 1: # entry limit
                if order.id not in self.positions: # this id is not already in positions
                    if order.id in self.pending_orders: # we are already in pending order
                        self.edit_pending_order(order, index)
                    elif order.id not in self.pending_orders: # we don't have pending open for this id, so we post entry limit
                        self.post_pending_order(order, index)
                        
                elif order.id in self.positions: # we are already in position but we can check right to edit sl & tp
                    self.edit_position(order, index)
                
        elif order.mode == 1: # exit market            
            if order.id in self.positions:
                self.exit_market(order.id, index)
            
        elif order.mode == 2: # cancel pending
            delAllowed = order.id in self.pending_orders
            if delAllowed:
                del self.pending_orders[order.id]
            
        elif order.mode == 3: # edit position
            if order.id in self.positions: # we are in position and we can check if we have the right to edit it
                self.edit_position(order, index)


    def upd_upnl(self, position, index):
        direction = position['direction']
        symbol = position['symbol']
        id_position = position['id']
        if direction == 1:
            upnl = (self.get_arr_value(symbol, 'ask_high', index) - position['entry_price']) / position['entry_price']
            if self.positions[id_position]['max_upnl'] < upnl:
                self.positions[id_position]['max_upnl'] = upnl
            if self.positions[id_position]['min_upnl'] > upnl:
                self.positions[id_position]['min_upnl'] = upnl
        elif direction == -1:
            upnl = (position['entry_price'] - self.get_arr_value(symbol, 'bid_low', index)) / position['entry_price']
            if self.positions[id_position]['max_upnl'] < upnl:
                self.positions[id_position]['max_upnl'] = upnl
            if self.positions[id_position]['min_upnl'] > upnl:
                self.positions[id_position]['min_upnl'] = upnl
        
            
    def check_tp(self, position, index):
        '''
        We assume LONG take-profit are triggered with cross with BID price.
        We assume SHORT take-profit are triggered with cross with ASK price.
        '''
        direction = position['direction']
        symbol = position['symbol']
        id_position = position['id']
        if (direction == 1 and self.get_arr_value(symbol, 'bid_high', index) > position['tp']) or (direction == -1 and self.get_arr_value(symbol, 'ask_low', index) < position['tp']):
            dic_trades = position.copy()
            dic_trades['exit_index'] = index
            dic_trades['exit_time'] = self.get_arr_value(symbol, 'time', index)
            dic_trades['exit_type'] = 'tp'
            dic_trades['exit_fill_iteration'] = index - dic_trades['entry_index']
            dic_trades['exit_fill_delay_sec'] = self.get_arr_value(symbol, 'time', index) - dic_trades['entry_time']
            dic_trades['exit_price'] = position['tp']
            dic_trades['exit_fee'] = self.get_maker_fee(symbol)
            dic_trades['total_fee'] = dic_trades['exit_fee'] + dic_trades['entry_fee']
            dic_trades['pnl_no_fee'] = position['direction'] * (dic_trades['exit_price'] - dic_trades['entry_price'])/ dic_trades['entry_price']
            dic_trades['pnl'] = dic_trades['pnl_no_fee'] - dic_trades['total_fee']
            dic_trades['pnl_usd'] = dic_trades['pnl'] * dic_trades['qty_in_usd']
            self.capital = self.capital + dic_trades['pnl_usd']
            dic_trades['capital'] = self.capital

            self.list_trades.append(dic_trades)
            self.nbs_trades += 1
            self.current_pnl += dic_trades['pnl']
            del self.positions[id_position]
        
        
    def check_sl(self, position, index):
        '''
        We assume LONG stop-loss are triggered with cross with BID price.
        We assume SHORT stop-loss are triggered with cross with ASK price.
        '''
        direction = position['direction']
        symbol = position['symbol']
        id_position = position['id']
        if (direction == 1 and self.get_arr_value(symbol, 'bid_low', index) < position['sl']) or  (direction == -1 and self.get_arr_value(symbol, 'ask_high', index) > position['sl']): 
            dic_trades = position.copy()
            dic_trades['exit_index'] = index
            dic_trades['exit_time'] = self.get_arr_value(symbol, 'time', index)
            dic_trades['exit_type'] = 'sl'
            dic_trades['exit_fill_iteration'] = index - dic_trades['entry_index']
            dic_trades['exit_fill_delay_sec'] = self.get_arr_value(symbol, 'time', index) - dic_trades['entry_time']
            dic_trades['exit_price'] = position['sl']
            dic_trades['exit_fee'] = self.get_taker_fee(symbol)
            dic_trades['total_fee'] = dic_trades['exit_fee'] + dic_trades['entry_fee']
            dic_trades['pnl_no_fee'] = position['direction'] * (dic_trades['exit_price'] - dic_trades['entry_price'])/ dic_trades['entry_price']
            dic_trades['pnl'] = dic_trades['pnl_no_fee'] - dic_trades['total_fee']
            dic_trades['pnl_usd'] = dic_trades['pnl'] * dic_trades['qty_in_usd']
            self.capital = self.capital + dic_trades['pnl_usd']
            dic_trades['capital'] = self.capital

            self.list_trades.append(dic_trades)
            self.nbs_trades += 1
            self.current_pnl += dic_trades['pnl']
            del self.positions[id_position]
            
        
    def check_filling(self, pending_order, index):
        '''
        We assume LONG limit are triggered with cross with ASK price.
        We assume SHORT limit are triggered with cross with BID price.
        '''
        direction = pending_order['direction']
        symbol = pending_order['symbol']
        posted_index = pending_order['posted_index']
        posted_time = pending_order['posted_time']
        price = pending_order['price']
        qty = pending_order['qty']
        qty_in_usd = pending_order['qty_in_usd']
        editable_position = pending_order['editable_position']
        if (direction == 1 and self.get_arr_value(symbol, 'ask_low', index) < price) or (direction == -1 and self.get_arr_value(symbol, 'bid_high', index) > price):
            position = {
                'symbol': symbol,
                'id': pending_order['id'],
                'entry_index': index,
                'entry_time': self.get_arr_value(symbol, 'time', index),
                'entry_price': price,
                'entry_fill_iteration': index - posted_index,
                'entry_fill_delay_sec': self.get_arr_value(symbol, 'time', index) - posted_time,
                'direction': direction,
                'entry_fee': self.get_maker_fee(symbol),
                'entry_type': 'limit',                
                "max_upnl": 0,
                "min_upnl": 0,
                'qty': qty,
                'qty_in_usd': qty_in_usd,
                'editable': editable_position
            }

            if 'tp' in pending_order:
                position['tp'] = pending_order['tp']
            if 'sl' in pending_order:
                position['sl'] = pending_order['sl']

            # append position
            self.positions[pending_order['id']] = position.copy()

            # delete previous pending
            del self.pending_orders[pending_order['id']]
            
        
    def compute_iteration_of_orders(self, list_orders, index, debug=False):
        
        if debug:
            print('\n\n ### order list:')
            print(self.datas.arr_order_lists[index])
            print('\n\n### iteration -',index)
            
            print('\n## pending:')
            print(pp(self.pending_orders))
            print('\n## positions:')
            print(pp(self.positions))
            print('\n## bid',self.get_arr_value('BTCUSD', 'bid_close', index),' ask:',self.get_arr_value('BTCUSD', 'ask_close', index))
            print('\n## pnl:\n',self.current_pnl)
        
        # update unrealized pnl
        list_positions = self.positions.items()
        for position_id,position in list(list_positions):
            self.upd_upnl(position, index) 
        
        if debug:
            print('\n\n ### POSITION POST UPD UPNL ###:')
            print('\n## positions:')
            print(pp(self.positions))
        
        # check pendng order filling
        list_pendings = self.pending_orders.items()
        for pending_order_id,pending_order in list(list_pendings):      
            self.check_filling(pending_order, index)
        
        # check take profits
        list_positions = self.positions.items()
        for position_id,position in list(list_positions):
            if 'tp' in position:
                self.check_tp(position, index)
              
        # check sl  
        list_positions = self.positions.items()
        for position_id,position in list(list_positions):
            if 'sl' in position:
                self.check_sl(position, index)
        
        # execute new orders
        for order in list_orders:
            self.compute_order(order, index)
        
        if debug:
            print('\n##### After actions #####')
            print('\n## pending:')
            print(pp(self.pending_orders))
            print('\n## positions:')
            print(pp(self.positions))
            print('\n## bid',self.get_arr_value('BTCUSD', 'bid_close', index),' ask:',self.get_arr_value('BTCUSD', 'ask_close', index))
            print('\n## pnl:\n',self.current_pnl)
            print('\n################################\n')


    def backtest(self, use_tqdm=True, debug_step = 0):
        if use_tqdm:
            pbar = tqdm(range(len(self.datas.arr_order_lists)))
        else:
            pbar = range(len(self.datas.arr_order_lists))

        if debug_step == 0:
            debug = False
        else:
            debug = True

        if debug:
            for i in pbar:
                self.compute_iteration_of_orders(self.datas.arr_order_lists[i], i, debug)
                if use_tqdm and i % 10000 == 0:
                    pbar.set_description_str(f'pnl: {round(100*self.current_pnl,1)}%')
                if i > debug_step:
                    break
        else:
            for i in pbar:
                self.compute_iteration_of_orders(self.datas.arr_order_lists[i], i)
                if use_tqdm and i % 10000 == 0:
                    pbar.set_description_str(f'pnl: {round(100*self.current_pnl,1)}%')
            
            
    def extract_metrics(self, preci='normal'): # preci can be 'pips', 'precent', or 'normal'
        df_trades = pd.DataFrame(self.list_trades)
        arr_pnl = df_trades.pnl.to_numpy()
        arr_capital_cum = self.init_capital + (df_trades.pnl.to_numpy() * df_trades.qty_in_usd.to_numpy()).cumsum()
        res = {}

        def get_max_drawdown(arr_cumsum):
            i = np.argmax(np.maximum.accumulate(arr_cumsum) - arr_cumsum) # end of the period
            if len(arr_cumsum[:i])>0:
                j = np.argmax(arr_cumsum[:i]) # start of period
            else:
                j = -1
            return (arr_cumsum[j] - arr_cumsum[i])/arr_cumsum[i]
        
        df_trades.loc[:,'date_exit'] = pd.to_datetime(df_trades.exit_time, unit='s')
        df_daily = df_trades.set_index('date_exit').resample('1D').agg({'pnl':'sum'}).reset_index()

        if preci == 'pips':
            mult = 10000
        elif preci == 'percent':
            mult = 100
        else:
            mult = 1

        res[0] = {
            "cumulative_pnl": mult * arr_pnl.sum(),
            "avg_pnl_per_trades": mult * arr_pnl.mean(),
            "sharpe_ratio_trades": arr_pnl.mean()/arr_pnl.std(),
            "profit_factor": - arr_pnl[arr_pnl>0].sum() / arr_pnl[arr_pnl<0].sum(),
            "accuracy_trades": len(arr_pnl[arr_pnl>0]) / len(arr_pnl),
            "proportion_sl": len(df_trades.loc[df_trades.exit_type=='sl']) / len(arr_pnl),
            "max_capital_drawdown": mult * get_max_drawdown(arr_capital_cum),
            "daily_return": mult * df_daily.pnl.mean(),
            "trades_per_day": len(arr_pnl) / len(df_daily),
            "cumulative_max_upnl": mult * df_trades.max_upnl.sum(),
            "cumulative_min_upnl": mult * df_trades.min_upnl.sum(),
            "avg_max_upnl_per_trade": mult * df_trades.max_upnl.mean(),
            "avg_min_upnl_per_trade": mult * df_trades.min_upnl.mean(),
            "avg_no_fee_pnl_per_trade": mult * df_trades.pnl_no_fee.mean(),
            "proportion_long": len(df_trades.loc[df_trades.direction == 1]) / len(df_trades),
            "preci": preci
        }
        return res


    def save_simple(self):
        source_dic_datas = self.datas.get_source_dict()
        metrics = self.extract_metrics()

        def source_dic_datas_to_UUID(source_dic_datas):
            txt = ''
            txt += str(source_dic_datas['start_year']) + '|'
            txt += str(source_dic_datas['start_month']) + '|'
            txt += str(source_dic_datas['end_year']) + '|'
            txt += str(source_dic_datas['end_month']) + '|'
            txt += '_ds_'
            for name, dataset in source_dic_datas['datasets'].items():
                txt += dataset['field'] + '~' + dataset['broker'] + '~' + dataset['instrument'] + '~' + dataset['symbol'] + '~' + dataset['timeframe'] + '|'
            txt += '_tr_'
            for name, transformer in source_dic_datas['transformers'].items():
                txt += transformer['name'] + '~' + str(len(transformer['function_str'])) + '~' + str(transformer['params']) + '|'
            txt
            for name, strategy in source_dic_datas['strategies'].items():
                txt += strategy['name'] + '~' + str(len(strategy['trigger_str'])) + '~' + str(strategy['params']) + '|'
            return txt

        # create csv if non existant
        if "res.csv" not in os.listdir('results/simple'):
            # list of column names 
            dict = {**metrics[0].copy(), **{"date":datetime.datetime.now(), "uuid":'test'}}
            field_names = [key for key in dict.keys()]
            pd.DataFrame(columns=field_names).to_csv('results/simple/res.csv', index=False)
        # create msgpack if non existant
        if "res.msgpack" not in os.listdir('results/simple'):
            dic_to_msgpack({}, 'results/simple/res.msgpack')

        # download msgpack
        res = msgpack_to_dic('results/simple/res.msgpack')
        uuid = source_dic_datas_to_UUID(source_dic_datas)
        if uuid not in res:

            # upload in csv
            dict = {**metrics[0].copy(), **{"date":datetime.datetime.now(), "uuid":uuid}}
            field_names = [key for key in dict.keys()]
            with open('results/simple/res.csv', 'a') as f_object:
                dictwriter_object = DictWriter(f_object, fieldnames=field_names)
                dictwriter_object.writerow(dict)
                f_object.close()

            # upload msg_back
            res[uuid] = {"uuid":uuid, "metrics":metrics, "source":source_dic_datas}
            dic_to_msgpack(res, 'results/simple/res.msgpack')


    def plot_standard_backtest_result(self):

        df_trades = pd.DataFrame(self.list_trades)
        df_trades.loc[:,'date_exit'] = pd.to_datetime(df_trades.exit_time, unit='s')
        df_daily = df_trades.set_index('date_exit').resample('1D').agg({'pnl':'sum'}).reset_index()
        df_weekly = df_trades.set_index('date_exit').resample('7D').agg({'pnl':'sum'}).reset_index()

        metrics_0 = self.extract_metrics()[0]

        # create fig subplot
        fig = make_subplots(rows=4, cols=1, 
                                    shared_xaxes=True, 
                                    vertical_spacing=0.1,
                                    specs=[[{"type": "scatter"}], # ploy pnl
                                           [{"type": "scatter"}], # daily pnl
                                           [{"type": "table"}], # metrics
                                           [{"type": "table"}]]) # params transformer

        # plot cumulative pnl
        fig.add_trace(go.Scatter(
            x=df_daily.date_exit,
            y=(df_daily.pnl).to_numpy().cumsum(),
            name="Cumulative pnl",
            line = {
                "color": rgb2hex(0,0,200)
            }
        ), row=1, col=1)

        # plot bar chart of daily pnl
        fig.add_trace(go.Bar(
            x=df_weekly.date_exit,
            y=(df_weekly.pnl).to_numpy(),
            name="Weekly pnl",
            #marker_color = rgb2hex(255,0,0),
            marker = {
                "color": rgb2hex(255,0,0),
                "line": {
                    "color": rgb2hex(255,0,0)
                }
            }
        ), row=2, col=1)

        # add metrics in a table
        list_key = []
        list_value = []
        for key,item in metrics_0.items():
            if type(item) is not str:
                list_value.append(str(round(item,5)))
            else:
                list_value.append(item)
            list_key.append(key)

        fig.add_trace(go.Table(
                header=dict(
                    values=list_key[:len(list_key)//2],
                    font=dict(size=8),
                    align="left"
                ),
                cells=dict(
                    values=list_value[:len(list_key)//2],
                    align = "left")
            ), row=3, col=1)

        # add metrics in a table
        fig.add_trace(go.Table(
                header=dict(
                    values=list_key[len(list_key)//2:],
                    font=dict(size=8),
                    align="left"
                ),
                cells=dict(
                    values=list_value[len(list_key)//2:],
                    align = "left")
            ), row=4, col=1)


        # edit layout config
        fig.update_layout(
            height = 600,
            width = 1200,
            showlegend = True,
            title_text = "Backtesting results",
            plot_bgcolor = rgb2hex(240,240,240), #"#21201f",
            paper_bgcolor = rgb2hex(240,240,240), #"21201f",
            font=dict(color= rgb2hex(30,30,30)), #'#dedddc'),
            dragmode='pan',
            hovermode='x unified'
        )

        # edit x axes config
        fig.update_xaxes(
            showgrid=False, 
            zeroline=False, 
            rangeslider_visible=False, 
            showticklabels=False, 
            spikemode='across', 
            spikesnap='data', 
            showline=False, 
            spikedash='solid'
        )
        return fig