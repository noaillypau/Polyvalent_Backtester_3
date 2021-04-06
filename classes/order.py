
'''
Order is the main order object
it can be:
    entry order / exit order / edit order/ edit position (sl, & tp) / cancel order

supported entry / exit types:
    market : standard market order
    limit : pending order, waiting to get filled

direction:
    long or short


when creating order object you must first specify the mode
then depending on the mod you may require differents argument

ex1: market order

order = Order(mode=Order.TYPE_market, qty=10, direction=1)

ex2: edit sl & tp
    
order = Order(mode=Order.MODE_edit_position, id_target=5, sl=12.3, tp=13.6)

'''


class Order():
    # tyep of order
    TYPE_market = 0
    TYPE_limit = 1
    # mode of action
    MODE_entry = 0
    MODE_exit = 1
    MODE_cancel = 2
    MODE_edit = 2
    # DIRECTION
    DIRECTION_long = 1
    DIRECTION_short = -1

    def __init__(self, mode, **kwargs):
        for key,value in kwargs.items():
            setattr(self, key, value)


class OrderEntryMarket(Order):
    '''
    Enter a new trade by sending a market order.
    Doesn't requiere the price (it will fill with bid/ask depending on direction)
    sl & tp are optional, but qty is necessary
    '''
    def __init__(self, id, direction, qty, symbol, tp=None, sl=None, editable_position=False):
        super(OrderEntryMarket, self).__init__(mode=0)
        self.mode = 0
        self.id = id
        self.type = 0
        self.direction = direction
        self.qty = qty
        self.symbol = symbol
        self.tp = tp
        self.sl = sl
        self.editable_position = editable_position

        self._dict = {'id':id, 'type':0, 'direction':direction, 'qty':qty, 'symbol':symbol, 'tp':tp, 'sl':sl, 'editable_position':editable_position}

    def __repr__(self):
        txt = 'Order Entry Market.'
        for key,item in self._dict.items():
            txt += f'\n  {key}: {item}'
        return txt


class OrderEntryLimit(Order):
    '''
    Enter a new trade by sending a limit order (pending untill filled). 
    Require a price. But tp and sl are optional.
    By putting editable_pending = True and sending a same order with same id, if the order is still pending
    then it will edit its price,tp & sl with current args
    By putting editable_position = True and sending a same order with same id, if the order is filled
    then it will edit its tp & sl with current args
    '''
    def __init__(self, id, direction, qty, symbol, price=None, tp=None, sl=None, editable_pending=False, editable_position=False):
        super(OrderEntryLimit, self).__init__(mode=0)
        self.mode = 0
        self.id = id
        self.type = 1
        self.direction = direction
        self.qty = qty
        self.symbol = symbol
        self.price = price
        self.tp = tp
        self.sl = sl
        self.editable_pending = editable_pending
        self.editable_position = editable_position

        self._dict = {'id':id, 'type':1, 'direction':direction, 'qty':qty, 'symbol':symbol, 'price':price, 'tp':tp, 'sl':sl, 'editable_pending':editable_pending, 'editable_position':editable_position}

    def __repr__(self):
        txt = 'Order Entry Limit.'
        for key,item in self._dict.items():
            txt += f'\n  {key}: {item}'
        return txt


class OrderExitMarket(Order):
    '''
    cancel all position with id of self.id with a market order
    '''
    def __init__(self, id):
        super(OrderExitMarket, self).__init__(mode=1)
        self.mode = 1
        self.id = id
        self.type = 0

        self._dict = {'id':id, 'type':0}

    def __repr__(self):
        txt = 'Order Exit Market.'
        for key,item in self._dict.items():
            txt += f'\n  {key}: {item}'
        return txt


class OrderCancelPending(Order):
    '''
    cancel all pending order with id of self.id
    '''
    def __init__(self, id):
        super(OrderCancelPending, self).__init__(mode=2)
        self.mode = 2
        self.id = id

        self._dict = {'id':id}

    def __repr__(self):
        txt = 'Order Cancel Pending.'
        for key,item in self._dict.items():
            txt += f'\n  {key}: {item}'
        return txt

class OrderEdit(Order):
    '''
    Edit only order
    if a position with the arg id is open, then edit it's content (sl, tp)
    '''
    def __init__(self, id, tp=None, sl=None):
        super(OrderEdit, self).__init__(mode=3)
        self.mode = 3
        self.id = id
        self.tp = tp
        self.sl = sl

        self._dict = {'id':id, 'tp':tp, 'sl':sl}

    def __repr__(self):
        txt = 'Order Edit Position.'
        for key,item in self._dict.items():
            txt += f'\n  {key}: {item}'
        return txt


        
