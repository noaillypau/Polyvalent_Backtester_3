General Infos
=========

Attempt to make the most polyvalent backtester possible, for all markets while staying accurate, easy to use and minimizing computing time as well as the necessary programming on the user side.

When testing a new strategy, one can often loose a lot of time building a new backtesting script, escpecially if the strategy uses non common features and logic.

Reducing the time writting thos scripts allows to test more strategy.

The goal of this repo is to make backtesting easier and faster by building a polyvalent script that is compatible with every kind of strategy. 





Table of contents
=================

<!--ts-->
   * [General infos](#general-infos)
   * [Table of contents](#table-of-contents)
   * [Installation](#installation)
   * [Historical data](#historical-data)
       * [MT5](#mt5)  
       * [Bybit](#bybit) 
       * [Other](#other) 
   * [Usage](#usage)
      * [Data](#data)
         * [Instantiation](#instantiation)  
         * [Add dataset](#add-dataset)      
      * [Transformer](#transformer)
      * [Strategies](#strategies)
      * [Compilation](#compilation)
      * [Grid Optimization](#grid-optimization)
      * [Smart Optimization](#smart-optimization)
   * [Object Documentation](#object-documentation) 
      * [Dataset](#dataset)
      * [Transformer](#transformer)
      * [Strategy](#Strategy)
      * [Order](#Order)
      * [Trader](#Trader)
      * [gridOpt](#gridOpt)
      * [smartOpt](#smartOpt)
   * [Dependency](#dependency)
   * [Todos](#todos)
<!--te-->


Installation
============

```shell
git clone https://github.com/noaillypau/polyvalent_backtester_v3
```

Historical data
===============

Historical datas is downloaded from official sources to assure no differences between backtesting and live datas.

For each source, tick data and 1min ohlc (if available) are downloaded on notebooks (one for each source) as files of 1month length.

Then for each source the data is classified, c.f example bellow:

 assetType | broker | instrument | symbol | timeframe | year | year-month.csv.gz |
 --- | --- | --- | --- | --- | --- | --- |
  Crypto | Bybit | Price | BTCUSD | 1min | 2020 | 2020-05.csv.gz |

MT5
-----

see notebook datas/mt5.ipynb

Bybit
-----

see notebook datas/bybit.ipynb

Other
-----

Usage
=====

Data
-----



### Instantiation

load config, and instance dataManager
```python
config = load_config('config.yml')

datas = Datas(config, 
              start_year = 2015,
              start_month = 1,
              end_year = 2021,
              end_month = 1)
```

### Add dataset

instantiation dataManager
```python
dataManager = DataManager(DataManager.Crypto)
```
Create dataset from datamanager
```python
dataset_btcusd = dataManager.BYBIT_TRADES_BTCUSD_1min
```

add dataset to data, precise name (identifier) and eventual resample
```python
datas.add_dataset(name='BTCUSD', 
                 dataset=dataManager.BYBIT_TRADES_BTCUSD_1min, 
                 timeframe = '30min')
```

eventually visualize all the added datasets
```python
print(datas.datasets)
```
```
BTCUSD
Dataset of Crypto:
  Broker: Bybit
  Instrument: trades
  Symbol: BTCUSD
  timeframe: 30min
  Path: D://Trading/Data/Crypto/Bybit/trades/BTCUSD/1min/
```



Transformer
-----


instantiation Transformer
```python
transformers = Transformers()
```

Create a transformation function and add transformer to transformers
```python
def function(dfs, params):
    '''
    transformer dfs here
    dfs is a dic of { key : pandas dataframe }
    with key being the string name of each dataset
    '''
        
    return dfs
    
transformers.add(name='bbands',
                 function=function, 
                 params={'period':20, 'mult':2, 'matype':0})
```

set transformers on data
```python
datas.set_transformers(transformers)
```


Strategies
-----

Each strategy consist on a trigger function, that will assert if actions are to take place or not, as well as a list of orders to send (list of actions).



Instantiation
```python
strategies = Strategies()
```

Create a trigger function that must always take the same arguments as ex bellow:
```python
def trigger(arrs, params, index):
    '''
    arrs is a dict of arrays, indexed by dataset name
    params is dict of params
    index is an int, current index on the backtesting
    
    trigger function must return a boolean
    '''
    
    if condition1 and condition2:
      return True
    
    return False
```

Create Orders objects (cf. Order doc)
```python
order1 = Order(id=5,
               mode=Order.MODE_edit_position, 
               id_target=3, 
               sl=12.3, 
               tp=13.6)
               

order2 = Order(id=3,
               mode=Order.Mode_entry, 
               type=Order.Type_market
               qty=500,
               direction=Order.DIRECTION_long,
               tp=15.4,
               limit_position=1)
```

Create a strategy object
```python
strategy = Strategy(dataset_name='BTCUSD',
                    trigger=trigger,
                    params={},
                    list_orders=[order1, order2])
```

add strategy to strategies
```python
strategies.add(name='strategy1',
               strategy=strategy)
```

set data.strategies
```python
datas.set_strategies(strategies)
```


Compilation
-----

One strategies, transformers and datasets are set, you can compile the data. It will import the datasets and apply transformers as well as extracting signals.
```python
datas.compile(from_datasets=True) # if from_datasets = False, will not reimport datasets (usefull to save computation time)
```

You can allso compile separately
```python
datas.compile_datasets()
datas.compile_transformers()
datas.compile_strategies()
```

Grid Optimization
-----

Module used to compute in sample/out sample optimization (naive method).

You can replace each parameter inputed in transformers or strategies by a list of value.

The grid Opt will then compute backtesting for each possibilities and take the best in sample result, then apply the best params found to do a backtesting on the out sample datasets.

Initialize the gridOpt object
```python
gidOpt = GridOpt(capital=10000, # same as in trader instance
		  datas=datas, # same as in trader instance
		  dic_list_params=dic_list_params, 
		  prop_in_sample=0.5,  # proportion of the datas used in the in sample
		  optimizer=GridOpt.OPT_sharpe_only # id of the optimizer. Opt_sharpe_only will only maximize sharpe ratio
		  ) 
```

run the grid optimization
```python
gidOpt.run(log=True, # logging mode
           use_multi_thread=True) # multi processing

best_config = gridOpt.get_best_config() # get config obtained with optimization within in sample
out_metrics = gridOpt.get_out_metrics() # get metrics of backtest within out sample
in_metrics = gridOpt.get_in_metrics() # get metrics of backtest within in sample

gidOpt.plot() # plot result

gidOpt.save() # save grid opt
```

Smart Optimization
-----

Module used to compute a smarter optimization than grid optimization using deep reinforcement learning.

Object Documentation
=====


Dataset
-----

Transformer
-----

Strategy
-----

Order
-----

Order object if defined with `id` and `mode` parameters.

`OrderEntryMarket`, `OrderEntryLimit`, `OrderExitMarket`, `OrderEdit` and `OrderCancelPending` are all implemented object that derive from `Order` object.
 
 ### market entry order
 
Example entry market order
```python
order = OrderEntryMarket(id=111, # id to locate the position
			 direction=1, # int 1 or -1, or Order.DIRECTION_long or Order.DIRECTION_short
                         qty=0.1, # int/float qty of contract to buy/sell
                         symbol = 'EURUSD') # name of the dataset on which order will be send
```

 Argument | Optional | Type | 
  --- | --- | --- | 
 id | False | int | 
 direction | False | int | 
 qty | False | float | 
 symbol | False | str | 
 tp | True | float | 
 sl | True | float | 
 editable_position | True | Bool | 
 
You do not need to specify the price, as it will buy at current ask price, or sell at current bid price.
 
 ### limit entry order
 
 Post a limit order, it will be stored in pending orders untill it is filled, then it will be considered as a position.
 
 You can cancel it, or edit price, take profir or stop loss values.
 
 However once it is filled you can only edit tp & sl.
 
Example entry limit order
```python
order = OrderEntryLimit(id=111, # id to locate the position
			direction=1, # int 1 or -1, or Order.DIRECTION_long or Order.DIRECTION_short
                         qty=0.1, # int/float qty of contract to buy/sell
                         price=0.0325,
                         tp=0.0332,
                         sl=0.0320,
                         editable_pending=True, # wether to allow edit of price/sl/tp untill it is filled
                         editable_position=True, # wether to allow edit of tp/sl once in position
                         symbol = 'ETHBTC') # name of the dataset on which order will be send
```

 Argument | Optional | Type | 
  --- | --- | --- | 
 id | False | int | 
 direction | False | int | 
 qty | False | float | 
 symbol | False | str | 
 price | False | float | 
 tp | True | float | 
 sl | True | float | 
 editable_pending | True | Bool | 
 editable_position | True | Bool | 
 
 If you want to edit the pending limit order, you can just send a new limit order with same id as an existing pending order, with different value for tp/sl/price
 
  ### cancel pending order
 
Cancel a pending order
 
Example cancel pending order
```python
order = OrderCancelPending(id=111) # id to locate the pending order
```

 Argument | Optional | Type | 
  --- | --- | --- | 
 id | False | int | 
 
   ### exit market order
 
Locate a position, and exit it with a market order.
 
Example exit market order
```python
order = OrderExitMarket(id=111) # id to locate the position
```

 Argument | Optional | Type | 
  --- | --- | --- | 
 id | False | int | 
 
   ### edit order
 
Locate a position and edit its tp/sl.
 
Example edit order
```python
order = OrderEdit(id=111,
		  tp=0.25
                  sl=0.21)
```

 Argument | Optional | Type | 
  --- | --- | --- | 
 id | False | int | 
 tp | True | float | 
 sl | True | float | 
 

Trader
-----

GridOpt
-----

SmartOpt
-----

Dependency
=====

Todos
=====

- [ ] remake the dataset module
	- [ ] make it more intuitive and flexible
- [ ] More datas
	- [ ] ftx -> trades datas to 1min ohlc (cf. bybit)
	- [ ] binance
	- [ ] bitfinex
	- [x] bitmex
- [ ] Grid Optimization
	- [ ] finish testing of grid optimization
	- [ ] clean code
- [ ] Smart Optimization
- [ ] Software ?

