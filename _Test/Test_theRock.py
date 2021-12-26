import theRock
import Keys

Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']


###############################################################################

def theRock_Private_Client():
    
    Key = Keys.theRock()
    client = theRock.PyRock.API(Key['key'], Key['secret'])
    return client
    
def theRock_Balances(Coin):  

    balances = theRock_Private_Client().AllBalances()
    print balances
    balances = balances['balances']
    
    for balance in balances:  
        if balance['currency'] == Coin:
            Coin_Balance = round(float(balance['trading_balance']), 8)
        elif balance['currency'] == Fiat[0]:
            Fiat_Balance = round(float(balance['trading_balance']), 2) 
        
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def theRock_MOQ():
    
    MOQ_Dict = {}
    for Coin in Coins:
        if Coin == 'BTC':   
            MOQ = 0.005
        elif Coin == 'LTC':
            MOQ = 0.01
        elif Coin == 'ETH':
            MOQ = 0.01
        MOQ_Dict.update({Coin: MOQ})     
    
    return {'Long': MOQ_Dict, 'Short': MOQ_Dict}

    
def theRock_Fees():
    
    pair = Coins[0] + Fiat[0] 
    funds = theRock_Private_Client().Funds()['funds']
    
    for fund in funds:
        if fund['id'] == pair:
            buy_fee = fund['buy_fee']
            sell_fee = fund['sell_fee']
            
    return {'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'currency': 'fiat'}
    
def theRock_Limit_Order(Coin, amount, side, price):
    
    leverage = 1.0
    
    if Coin == 'BTC':
        Amount = int(amount*1000) / 1000.0 # round down to 3 d.p.
        Amount = '%.3f' %(Amount)
    elif Coin == 'LTC':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
        Amount = '%.2f' %(Amount)
    elif Coin == 'ETH':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
        Amount = '%.2f' %(Amount)
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(Amount),
                                                side, str(price), leverage)
                                                
    print 'Message from theRock: ' + str(Order)
#    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Market_Order(Coin, amount, side):
    
    leverage = 1.0
    
    if Coin == 'BTC':
        Amount = int(amount*1000) / 1000.0 # round down to 3 d.p.
        Amount = '%.3f' %(Amount)
    elif Coin == 'LTC':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
        Amount = '%.2f' %(Amount)
    elif Coin == 'ETH':
        Amount = int(amount*100) / 100.0 # round down to 2 d.p.
        Amount = '%.2f' %(Amount)

    
    if side == 'buy':
            price = TheRock['Prices'][Coin]['entry_buy'] * 1+0.0005 # beats market price
    elif side == 'sell':
            price = TheRock['Prices'][Coin]['entry_sell'] * 1-0.0005 # beats market price
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().PlaceOrder(pair, str(Amount),
                                                side, str(price), leverage)
                                                
    print 'Message from theRock: ' + str(Order)
#    log.write('\nMessage from theRock: ' + str(Order))
    
    return Order
    
def theRock_Check_Order(Coin, ref):
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().ListOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
#    log.write('\nMessage from theRock: ' + str(Order))    
    
    return Order
    
def theRock_Orderbook(Coin):
    
    pair = Coin.lower() + Fiat[0].lower()
    client = theRock_Private_Client()
    Orderbook = client.OrderBook(pair)
    
    Asks_1 = Orderbook['asks']    
    Asks = []
    
    for ask in Asks_1:
        Asks.append([float(ask['price']), float(ask['amount'])])
    
    Bids_1 = Orderbook['bids']    
    Bids = []
    
    for bid in Bids_1:
        Bids.append([float(bid['price']), float(bid['amount'])])
    
    return (Asks, Bids)
    
def theRock_Filled(Coin, Order):
    
    Order_ID = Order['ID']

    isFilled = theRock_Check_Order(Coin, Order_ID)['status']
    
    if  isFilled == 'executed':
        Filled = True
    else: Filled = False
    
    return Filled
    
def theRock_Cancel_Order(Coin, ref):
    
    pair = Coin.lower() + Fiat[0].lower()
    Order = theRock_Private_Client().CancelOrder(pair, ref)
    
    print 'Message from theRock: ' + str(Order)
#    log.write('\nMessage from theRock: ' + str(Order)) 
    
    if Order['status'] == 'deleted':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
        
    return Order_Cancelled


###############################################################################
    
theRock_Balances('BTC')