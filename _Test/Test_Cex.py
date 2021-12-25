import cexapi

import Keys

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

def Cex_Private_Client(query, params={}):
    
    Key = Keys.Cex()
    Cex_API = cexapi.cexapi.API(Key['user'],Key['key'],Key['secret'])
    client = Cex_API.api_call(query, params, private=1)
    return client
    
def Cex_Fees():
    pair = pair1[0] + ':' + pair2
    fees = Cex_Private_Client('get_myfee')['data'][pair]
    
    return {'buy_maker_fee': float(fees['buyMaker']), 
            'sell_maker_fee': float(fees['sellMaker']),
            'buy_fee': float(fees['buy']),
            'sell_fee': float(fees['sell'])}
         
def Cex_Balances():   

    balance = Cex_Private_Client('balance')
        
    btc = round(float(balance['BTC']['available']),8)
    eur = round(float(balance['EUR']['available']),2)
    
    return {'BTC': btc, 'EUR': eur}
    
def Cex_Position(Coin, amount, side, leverage):
    
    pair = Coin + '/' + pair2
    
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'
    
    if leverage == 0.0:
        
        params = {'ptype': side,
                  'anySlippage': 'false',
                  'symbol': Coin,
                  'amount': str(amount)}
    else:
        
        params = {'ptype': side,
                  'anySlippage': 'false',
                  'symbol': Coin,
                  'amount': str(amount),
                  'leverage': str(leverage)} # 2 or 3 times             
    
    Order = Cex_Private_Client('open_position/'+pair, params)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Cex_Limit_Order(amount, side, price):
    
    pair = pair1[0] + '/' + pair2
    
    params = {'type': side,
              'amount': str(amount), 
              'price': str(price)}
              
    Order = Cex_Private_Client('place_order/'+pair, params)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Cex_Market_Order(amount, side):
    
    pair = pair1[0] + '/' + pair2
    
    params = {'type': side,
              'order_type': "market",
              'amount': str(amount)} 

              
    Order = Cex_Private_Client('place_order/'+pair, params)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Cex_Check_Order(ref):    
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('get_order', params)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
  

def Cex_Orderbook():
    
    pair = pair1[0] + '/' + pair2
    Orderbook = Cex_Private_Client('order_book/'+pair+'/')
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
    
def Cex_Filled(Order):
    
    Order_ID = Order['id']
    
    isFilled = Cex_Check_Order(Order_ID)['remains']
    
    if float(isFilled) > 0:
        Filled = False
    else: Filled = True
    
    return Filled
    
def Cex_Cancel_Order(ref):
    
    params = {'id': ref}
    
    Order = Cex_Private_Client('cancel_order', params)
    
#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    if Order == 'True':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled


#print Cex_Position(pair1[0], 0.008, 'sell', 2) # mminimum is 0.05

print Cex_Orderbook()
