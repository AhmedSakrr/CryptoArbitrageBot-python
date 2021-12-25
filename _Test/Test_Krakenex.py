import krakenex
import Keys
import time

Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']


def Kraken_Private_Client(query, params={}):
    
    Key = Keys.Kraken()
    client = krakenex.API(Key['key'],Key['secret']).query_private(query,params)
    return client
    
def Kraken_Fees():
    
    if Coins[0] == 'BTC':
        Coin = 'XBT'
    
    pair = 'X'+Coin+'Z'+Fiat[0]
    
    API = krakenex.API()
    fees = API.query_public('AssetPairs', {'info': 'fees'})['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees'][0][1]),
            'buy_maker_fee': float(fees['fees_maker'][0][1]),
            'sell_maker_fee': float(fees['fees_maker'][0][1])}
         
def Kraken_Balances(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    balance = Kraken_Private_Client('Balance')['result']
    
    Coin_Balance = round(float(balance['X'+coin]), 8)
    Fiat_Balance = round(float(balance['ZEUR']), 2)

    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
#def Kraken_Limit_Order(Coin, amount, side, price, leverage):
#    
#    if Coin == 'BTC':
#        coin = 'XBT'
#    else: coin = Coin
#    
#    pair = 'X'+coin+'Z'+Fiat[0]
#    
#    if leverage == 0.0:        
#    
#        params = {'pair': pair,
#                  'type': side,
#                  'ordertype': 'limit',
#                  'price': str(price),
#                  'volume': str(amount)} # 2 to 5 times
#    else:
#        
#        params = {'pair': pair,
#                  'type': side,
#                  'ordertype': 'limit',
#                  'price': str(price),
#                  'volume': str(amount),
#                  'leverage': str(leverage)} # 2 to 5 times             
#    
#    Order = Kraken_Private_Client('AddOrder', params)
#
#    print 'Message from Kraken: ' + str(Order)
##    log.write('\nMessage from Kraken: ' + str(Order)) 
#    
#    return Order


def Kraken_Limit_Order(Coin, amount, side, price, leverage):
        
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    price = round(price, 1)
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'limit',
                  'price': str(price),
                  'volume': str(amount)} # 2 to 5 times
    else:
        
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'limit',
                  'price': str(price),
                  'volume': str(amount),
                  'leverage': str(leverage)} # 2 to 5 times  
    
    print params
    
    Order = Kraken_Private_Client('AddOrder', params)

    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order

    
def Kraken_Market_Order(Coin, amount, side, leverage):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    if leverage == 0.0:        
    
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount),}
    else:
        
        params = {'pair': pair,
                  'type': side,
                  'ordertype': 'market',
                  'volume': str(amount),
                  'leverage': str(leverage)} # 2 to 5 times
              
    Order = Kraken_Private_Client('AddOrder', params)

    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Check_Order(ref):    
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('QueryOrders', params)

    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
  
def Kraken_Orderbook(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    API = krakenex.API()    
    Orderbook = API.query_public('Depth', {'pair': pair})['result'][pair]
    
    Asks = Orderbook['asks']    
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Kraken_Filled(Order):
    
    Order_ID = Order['ID']
    
    isFilled = Kraken_Check_Order(Order_ID)['result'][Order_ID]['status']
    
    if str(isFilled) == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def Kraken_Cancel_Order(ref):
    
    params = {'txid': ref}
    
    Order = Kraken_Private_Client('CancelOrder', params)
    
    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    if Order['result']['count'] == 1:
        Order_Cancelled = True
    
    return Order_Cancelled
    
#print Kraken_Balances('BTC')
    
#print Kraken_Limit_Order('BTC', 0.005, 'sell', 6900.00, str(2))
    
def Kraken_Trades_History():
        
    minutes_ago = 60
    time_now = time.time()

    
    params = {'start': time.time() - minutes_ago*60,
              'end': time_now}
        
    Orders = Kraken_Private_Client('TradesHistory', params)
    
    print 'Message from Kraken: ' + str(Orders)
    
    return Orders
    
def Kraken_Open_Orders():
        
    params = {}
        
    Orders = Kraken_Private_Client('OpenOrders', params)
    
    print 'Message from Kraken: ' + str(Orders)
    
    if Orders['result']['open']:
    
        return True
        
    else:
        return False

def Kraken_Closed_Orders():
        
    params = {}
        
    Orders = Kraken_Private_Client('ClosedOrders', params)
    
    print 'Message from Kraken: ' + str(Orders)
    
    return Orders
    
def Kraken_Open_Positions():
        
    params = {}
        
    Orders = Kraken_Private_Client('OpenPositions', params)
    
    print 'Message from Kraken: ' + str(Orders)
    
    if Orders['result']:
    
        return True
        
    else:
        return False
    
print Kraken_Balances('BTC')

