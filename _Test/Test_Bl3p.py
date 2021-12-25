import bl3p

import Keys

Key = Keys.Bl3p()

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

Coins = ['BTC', 'LTC', 'ETH']
#Coins = ['BTC']
Fiat = ['EUR']


###############################################################################

def Bl3p_Private_Client():
    key = Keys.Bl3p()    
    client = bl3p.Client.Private(key['key'], key['secret'])
    return client

def Bl3p_Balances(Coin):    

    balances = Bl3p_Private_Client().getBalances()
    
    Coin_Balance =  round(float(balances['data']['wallets'][Coin]['available']['value']),2)    
    Fiat_Balance = round(float(balances['data']['wallets'][Fiat[0]]['available']['value']), 8)
    
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Bl3p_MOQ(Coin):
        
    if Coin == 'BTC':
        MOQ = 0.0001
    elif Coin == 'LTC':
        MOQ = 0.001
    else:
        MOQ = 0.001
        
    return {Coin: MOQ}
    
def Bl3p_Fees():
    
    balances = Bl3p_Private_Client().getBalances()    
    fee = float(balances['data']['trade_fee']) # plus 0.01eur per trade
    
    return {'buy_fee': fee, 'sell_fee': fee}
    
def Bl3p_Limit_Order(Coin, amount, side, price):
    
    pair = Coin + Fiat[0]
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addOrder(pair, str(order_side), 
                                           int(amount), int(price))

    print 'Message from Bl3p: ' + str(Order)
#    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Market_Order(Coin, amount, side):
    
    pair = Coin + Fiat[0]
    
    if side == 'buy':
        order_side = 'bid'
    if side == 'sell':
        order_side = 'ask'
    
    Order = Bl3p_Private_Client().addMarketOrder(pair, str(order_side), int(amount))

    print 'Message from Bl3p: ' + str(Order)
#    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order
    
def Bl3p_Check_Order(Coin, ref):
    
    pair = Coin + Fiat[0]    
    Order = Bl3p_Private_Client().checkOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
#    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    return Order

    
def Bl3p_Orderbook(Coin):
    
    pair = Coin + Fiat[0]
    client = Bl3p_Private_Client()
    Orderbook = client.FullOrderbook(pair)['data']
    
#    print Orderbook
    
    Asks_1 = Orderbook['asks']
    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price_int'])/100000, 
                     float(ask['amount_int'])/100000000*float(ask['count'])])   
    
    Bids_1 = Orderbook['bids']
    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price_int'])/100000, 
                     float(bid['amount_int'])/100000000*float(bid['count'])])
    
    return (Asks, Bids)
    
def Bl3p_Filled(Coin, Order):
    
    Order_ID = Order['ID'] 
    
    isFilled = str(Bl3p_Check_Order(Coin, Order_ID)['data']['status'])
    
    if  isFilled == 'closed':
        Filled = True
    else: Filled = False
    
    return Filled
        
def Bl3p_Cancel_Order(Coin, ref):
    
    pair = Coin + Fiat[0]    
    Order = Bl3p_Private_Client().cancelOrder(pair, ref)
    
    print 'Message from Bl3p: ' + str(Order)
#    log.write('\nMessage from Bl3p: ' + str(Order)) 
    
    if Order['result'] == 'success':
        Order_Cancelled = True

    return Order_Cancelled
    
print Bl3p_Orderbook('BTC')