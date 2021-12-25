import Keys
import GDAX

Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']

def GDAX_Private_Client():
    
    key = Keys.GDAX()        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
    return client

def Gdax_Fees():    

    fills = GDAX_Private_Client().getFills()[0] # get latest filled order
        
    buy = []    
    for fill in fills:     
    
            if fill['side'] == 'buy':
                buy.append(fill)
                buy_fee_eur = float(buy[0]['fee'])
                buy_price = float(buy[0]['price'])
                buy_size = float(buy[0]['size'])
                buy_fee = (buy_fee_eur / (buy_size*buy_price)) * 100
                
    sell_fee = 0 # fee for market makers is zero

    return {'buy_fee': buy_fee,
            'sell_fee': sell_fee,
            'currency': 'fiat'}
    
def Gdax_MOQ(Coin):
        
    if Coin == 'BTC':
        MOQ = 0.01
    elif Coin == 'ETH':
        MOQ = 0.01
    elif Coin == 'LTC':
        MOQ = 0.01
        
    return {Coin: MOQ}

def Gdax_Balances(Coin):
    
    key = Keys.GDAX()
        
    client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
    accounts = client.getAccounts()
    
    for account in accounts:
        if account['currency'] == Coin:
            Coin_Balance = round(float(account['balance']), 8)  
    
    for account in accounts:
        if account['currency'] == Fiat[0]:
            Fiat_Balance = round(float(account['balance']), 2)
            
    return {Coin: Coin_Balance, Fiat[0]: Fiat_Balance}
    
def Gdax_Limit_Order(Coin, amount, side, price): #, margin): waiting to be margin approved
    
    pair = Coin+ '-' + Fiat[0]
    
    params = {'type': 'limit',
              'product_id': pair,
              'side': side,
              'price': str(price),
              'size': str(round(amount, 8))}
              #'overdraft_enabled': str(margin)} waiting to be margin approved

    Order = GDAX_Private_Client().order(params)

    print 'Message from Gdax: ' + str(Order)
#    log.write('\nMessage from Gdax: ' + str(Order)) 

    return Order
    
def Gdax_Market_Order(Coin, amount, side): #, margin): waiting to be margin approved
    
    pair = Coin+ '-' + Fiat[0]
    
    params = {'type': 'market',
              'product_id': pair,
              'side': side,
              'size': str(amount)}
              #'overdraft_enabled': str(margin)} waiting to be margin approved

    Order = GDAX_Private_Client().order(params)

    print 'Message from Gdax: ' + str(Order)
#    log.write('\nMessage from Gdax: ' + str(Order)) 

    return Order
    
def Gdax_Check_Order(ref):    
    
    Order = GDAX_Private_Client().getOrder(ref)

    print 'Message from Gdax: ' + str(Order)
#    log.write('\nMessage from Gdax: ' + str(Order)) 
    
    return Order    
    
def Gdax_Orderbook(Coin):
    
    pair = Coin+ '-' + Fiat[0]   
    public_client = GDAX.PublicClient(product_id = pair)   
    Orderbook = public_client.getProductOrderBook(level = 3)
    
    Asks = Orderbook['asks']
    Bids = Orderbook['bids']
    
    return (Asks, Bids)
    
def Gdax_Filled(Order):
    
    Order_ID = Order['ID']
    
    Filled = Gdax_Check_Order(Order_ID)['settled']
        
    return Filled
    
def Gdax_Cancel_Order(ref):    
    
    Order = GDAX_Private_Client().cancelOrder(ref)
    
    print 'Message from Gdax: ' + str(Order)
#    log.write('\nMessage from Gdax: ' + str(Order)) 
    
    if Order[0] == 'ref':
        Order_Cancelled = True
    else:
        Order_Cancelled = False
    
    return Order_Cancelled


Order = {'ID': 'e18508ef-bb7f-438f-adcf-f1fe7d916679'}

a = Gdax_Filled(Order)