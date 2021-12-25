import quoinex

import Keys

Key = Keys.Quoinex()

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'


###############################################################################

def Quoinex_Private_Client():
    
    Key = Keys.Quoinex()
    client = quoinex.api.Client(Key['Key'], Key['Secret'])
    return client
    
def Quoinex_Orderbook():
    
    pair = (pair1[0], pair2)
    
    API = quoinex.api.Client()
        
    Orderbook = API.get_orderbook(pair)
        
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['sell_price_levels']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['buy_price_levels']]
    
#    for i in range(0,3):
#        Asks.pop(0) # fixes bug in API data
     
    return (Asks, Bids)
    
def Quoinex_Fees():
    
    pair = (pair1[0], pair2)
    
    info = Quoinex_Private_Client().get_product_info(pair)
        
    buy_fee = info['taker_fee']
    sell_fee = info['taker_fee']
    buy_maker_fee = info['maker_fee']
    sell_maker_fee = info['maker_fee']
    
    return {'buy_fee': float(buy_fee), 
            'sell_fee': float(sell_fee),
            'buy_maker_fee': float(buy_maker_fee),
            'sell_maker_fee': float(sell_maker_fee)}

def Quoinex_Balances(): 

    balances = Quoinex_Private_Client().get_balances()
    
    for balance in balances:
        if balance['currency'] == pair1[0]:
            btc = round(float(balance['balance']), 8)
            
    for balance in balances:
        if balance['currency'] == pair2:
            eur = round(float(balance['balance']), 2)        
    
    return {'BTC': btc, 'EUR': eur}
    
def Quoinex_Limit_Order(amount, side, price, leverage):
    
    pair = (pair1[0], pair2)
    
    ordertype = 'limit'
    
    Order = Quoinex_Private_Client().place_limit_order(pair, ordertype, amount, side, price, leverage)

#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def Quoinex_Market_Order(amount, side, leverage):
    
    pair = (pair1[0], pair2)
    
    ordertype = 'market'

    Order = Quoinex_Private_Client().place_market_order(pair, ordertype, amount, side, leverage)

#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def Quoinex_Check_Orders(ref):
        
    Order = Quoinex_Private_Client().get_order(ref)

#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order 
    
def Quoinex_Filled(Order):
    
    quantity = Order['quantity']
    filled_quantity = Order['filled_quantity']
    
    if filled_quantity == quantity:
        Filled = True
    else: Filled = False
    
    return Filled

def Quoinex_Cancel_Order(ref):
    
    Order = Quoinex_Private_Client().cancel_order(ref)
        
#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    if Order['status'] == 'cancelled':
        Order_Cancelled = True
    
    return Order_Cancelled
    
def Quoinex_Update_Order(ref, price):
    
    Order = Quoinex_Private_Client().update_short(ref, price)
    
        
#    print 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    

    return Order
    
#print Quoinex_Limit_Order(0.01248, 'sell', 6000, 1)
    
#Quoinex_Cancel_Order(112573650)
    
#Order = Quoinex_Check_Orders(112573650)
#print Quoinex_Filled(Order)

#print Quoinex_Orderbook()

print Quoinex_Market_Order(0.01, 'sell', 2)

#print Quoinex_Update_Order(1676539, 15000)
