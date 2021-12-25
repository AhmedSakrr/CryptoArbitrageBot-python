import bitbay

import Keys

Key = Keys.Bitbay()

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'


###############################################################################

def Bitbay_Private_Client():
    
    Key = Keys.Bitbay()
    client = bitbay.api.Client(Key['Key'], Key['Secret'])
    return client
    
def Bitbay_Orderbook():
    
    pair = pair1[0] + pair2
    
    Orderbook = Bitbay_Private_Client().get_orderbook(pair)
    
    print((Orderbook))
    
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['asks']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['bids']]
     
    return (Asks, Bids)
    
def Bitbay_Fees():    
    
    info = Bitbay_Private_Client().get_info()
    fee = info['fee']
    
    return {'buy_fee': float(fee), 
            'sell_fee': float(fee)}
         
def Bitbay_Balances(): 

    balances = Bitbay_Private_Client().get_info()  
    print(balances)

    btc = round(float(balances['balances'][pair1[0]]['available']), 8)
    eur = round(float(balances['balances'][pair1[0]]['available']), 8)
    
    return {'BTC': btc, 'EUR': eur}
    
def Bitbay_Limit_Order(amount, side, price):
    
    pair = (pair1[0], pair2)
    
    Order = Bitbay_Private_Client().place_order(pair, amount, side, price)

#    print( 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def Bitbay_Market_Order(amount, side):
    
    pair = (pair1[0], pair2)
    
    if side == 'buy':
            price = BitBay['entry_buy'] * 1+0.00005
    elif side == 'sell':
            price = BitBay['entry_sell'] * 1-0.00005
              
    Order = Bitbay_Private_Client().place_order(pair, amount, side, price)

#    print( 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def Bitbay_Check_Orders():
        
    Order = Bitbay_Private_Client().get_order()

#    print( 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Order
    
def Bitbay_Check_Transactions():
        
    Transactions = Bitbay_Private_Client().get_transactions()

#    print( 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    return Transactions
    
    
def Bitbay_Filled(Order):
    
    Order_ID = Order['order_id']
    
    Orders = Bitbay_Check_Orders()
    
    for item in Orders:
        if item['order_id'] == Order_ID:
            
            isFilled = item['status']
    
    if str(isFilled) == 'inactive':
        Filled = True
    else: Filled = False
    
    return Filled

def Bitbay_Cancel_Order(ref):
    
    Order = Bitbay_Private_Client().cancel_order(ref)
    
#    print( 'Message from Bitbay: ' + str(Order)
#    log.write('\nMessage from Bitbay: ' + str(Order)) 
    
    if Order['success'] == 1:
        Order_Cancelled = True
    
    return Order_Cancelled   
    
print(Bitbay_Orderbook())