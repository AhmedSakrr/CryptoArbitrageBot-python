import kraken
import Keys

Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']


def Kraken_Private_Client(params={}):
    
    Key = Keys.Kraken()
    client = kraken.api.Client(key = Key['key'], secret = Key['secret'])
    return client
    
def Kraken_Fees():
    
    Coin = Coins[0]
    
    if Coins[0] == 'BTC':
        Coin = 'XBT'
    
    pair = 'X'+Coin+'Z'+Fiat[0]
    
    Client = kraken.api.Client()
    fees = Client.get_info(pair)['result'][pair]
    
    return {'buy_fee': float(fees['fees'][0][1]), 
            'sell_fee': float(fees['fees'][0][1]),
            'buy_maker_fee': float(fees['fees_maker'][0][1]),
            'sell_maker_fee': float(fees['fees_maker'][0][1])}
         
def Kraken_Balances(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
        
    balance = Kraken_Private_Client().get_balances()['result']
        
    Coin_Balance = round(float(balance['X' + coin]), 8)
    Fiat_Balance = round(float(balance['Z' + Fiat[0]]), 2)

    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}

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
        
    Order = Kraken_Private_Client().place_order(params)

    print ('Message from Kraken: ' + str(Order))
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
              
    Order = Kraken_Private_Client().place_order(params)

    print ('Message from Kraken: ' + str(Order))
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Kraken_Check_Order(ref):    
        
    Order = Kraken_Private_Client().query_order(ref)

    print ('Message from Kraken: ' + str(Order))
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
  
def Kraken_Orderbook(Coin):
    
    if Coin == 'BTC':
        coin = 'XBT'
    else: coin = Coin
    
    pair = 'X'+coin+'Z'+Fiat[0]
    
    Orderbook = Kraken_Private_Client().get_orderbook(pair)['result'][pair]
        
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
        
    Order = Kraken_Private_Client().cancel_order(ref)
    
    print ('Message from Kraken: ' + str(Order))
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    if Order['result']['count'] == 1:
        Order_Cancelled = True
    
    return Order_Cancelled
    
  
#def Kraken_Trades_History():
#        
#    minutes_ago = 60
#    time_now = time.time()
#
#    
#    params = {'start': time.time() - minutes_ago*60,
#              'end': time_now}
#        
#    Orders = Kraken_Private_Client('TradesHistory', params)
#    
#    print 'Message from Kraken: ' + str(Orders)
#    
#    return Orders
#    
def Kraken_Open_Orders():
                
    Orders = Kraken_Private_Client().open_orders()
    
    print ('Message from Kraken: ' + str(Orders))
    
    if Orders['result']['open']:
    
        return True
        
    else:
        return False

def Kraken_Closed_Orders():
                
    Orders = Kraken_Private_Client().closed_orders()
    
    print ('Message from Kraken: ' + str(Orders))
    
    return Orders
    
def Kraken_Open_Positions():
                
    Orders = Kraken_Private_Client().open_positions()
    
    print ('Message from Kraken: ' + str(Orders))
    
    if Orders['result']:
    
        return True
        
    else:
        return False
        
print (Kraken_Balances('BTC'))
    
#Price = float(Kraken_Check_Order('OLGCGX-VR7AG-YZXXOV')['result']['OLGCGX-VR7AG-YZXXOV']['price'])

