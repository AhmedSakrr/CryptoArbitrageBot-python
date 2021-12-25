import wex

import Keys

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

def Wex_Private_Client(query, **params):
    
    Key = Keys.Wex()
    client = wex.api.TradeAPIv1(Key).call(query, **params)
    return client
    
def Wex_Fees():    
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    api = wex.api.PublicAPIv3()
    fee = api.call('info')['pairs'][pair]['fee']
    
    return {'buy_fee': float(fee), 
            'sell_fee': float(fee)}
         
def Wex_Balances(): 

    balances = Wex_Private_Client('getInfo')['funds']   

    btc = round(float(balances['btc']),8)
    eur = round(float(balances['eur']),2)
    
    return {'BTC': btc, 'EUR': eur}
    
def Wex_Limit_Order(amount, side, price):
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    Order = Wex_Private_Client('Trade',pair=pair,type=side,amount=amount,rate=price)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Wex_Market_Order(amount, side):
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    if side == 'buy':
        price = 0.1
    elif side == 'sell':
        price = 1.0e8
              
    Order = Wex_Private_Client('Trade',pair=pair,type=side,amount=amount,rate=price)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Wex_Check_Order(ref):
        
    Order = Wex_Private_Client('OrderInfo', order_id=ref)

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Wex_Check_Transactions():
        
    Order = Wex_Private_Client('TransHistory')

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
def Wex_Active_Orders():
        
    Order = Wex_Private_Client('ActiveOrders')

#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    return Order
    
  
def Wex_Orderbook():
    
    pair = pair1[0].lower()+'_'+pair2.lower()
    
    API = wex.api.PublicAPIv3()
    
    Orderbook = API.call('depth/'+pair)[pair]
    
    Asks = [[float(i[0]), float(i[1])] for i in Orderbook['asks']]
    Bids = [[float(i[0]), float(i[1])] for i in Orderbook['bids']]
     
    return (Asks, Bids)
    
    
def Wex_Filled(Order):
    
    # Order ID's not relaying back from sever so this code is broken at the moment
    
#    Order_ID = Order['order_id']
#    
#    isFilled = Wex_Check_Order(Order_ID)['status']
#    
#    if str(isFilled) == 1:
#        Filled = True
#    else: Filled = False
#    
#    return Filled
    
    Order_ID = Order['order_id']
    
    try:
        Active_Orders = Wex_Active_Orders()
        
    except:
        return True # No active orders, so must have filled
        
    else:
        Orders = Active_Orders['return']
        for order in Orders:
            try:
                order[Order_ID]                
            
            except:
                return True # No Order found so must have filled
                
            else:
                return False # Still active so has not filled

def Wex_Cancel_Order(ref):
    
    Order = Wex_Private_Client('CancelOrder', order_id=ref)
    
#    print 'Message from Kraken: ' + str(Order)
#    log.write('\nMessage from Kraken: ' + str(Order)) 
    
    if Order[ref] == ref:
        Order_Cancelled = True
    
    return Order_Cancelled
         
print Wex_Filled({'order_id':'0'})