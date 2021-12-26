import bitfinex
import Keys
import time


Coins = ['BTC', 'LTC', 'ETH']
Fiat = ['EUR']


###############################################################################

def Bitfinex_Private_Client():
    
    Key = Keys.Bitfinex()
    client = bitfinex.api.Client(Key['key'], Key['secret'])
    return client
    
def Bitfinex_Orderbook(Coin):
    
    pair = Coin.lower() + Fiat[0].lower()
    
    Orderbook = Bitfinex_Private_Client().get_orderbook(pair)
    
    Asks = [[float(i['price']), float(i['amount'])] for i in Orderbook['asks']]
    Bids = [[float(i['price']), float(i['amount'])] for i in Orderbook['bids']]
    
    return (Asks, Bids)

#print(Bitfinex_Orderbook()


def Bitfinex_Fees():
        
    fees = Bitfinex_Private_Client().get_fees()[0]
    print(fees)
    
    return {'buy_fee': float(fees['taker_fees']), 
            'sell_fee': float(fees['taker_fees']),
            'buy_maker_fee': float(fees['maker_fees']),
            'sell_maker_fee': float(fees['maker_fees'])}
    
#print(Bitfinex_Fees()
    
def Bitfinex_MOQ(Coin):
    
    pair = Coin.lower() + Fiat[0].lower() 
    
    MOQs = Bitfinex_Private_Client().get_moqs()
    
    for MOQ in MOQs:
        if MOQ['pair'] == pair:        
            return {Coin: MOQ['minimum_order_size']}

#print(Bitfinex_MOQ('BTC')
    
def Bitfinex_Wallet_Transfer(Coin, amount, price, leverage):
    
    client = Bitfinex_Private_Client()

    balances = Bitfinex_Private_Client().get_balances()
    
    print(balances)
    
    Balances = {'coin_balance_exchange': 0.0,
                'coin_balance_margin': 0.0,
                'fiat_balance_exchange': 0.0,
                'fiat_balance_margin': 0.0}
    
    for balance in balances:
        
        if balance['currency'] == Coin.lower() and balance['type'] == 'exchange':
            Balances.update({'coin_balance_exchange': float(balance['available'])})
            
        elif balance['currency'] == Coin.lower() and balance['type'] == 'trading':
            Balances.update({'coin_balance_margin': float(balance['available'])})
            
        elif balance['currency'] == Fiat[0].lower() and balance['type'] == 'exchange':
            Balances.update({'fiat_balance_exchange': float(balance['available'])})
            
        elif balance['currency'] == Fiat[0].lower() and balance['type'] == 'trading':
            Balances.update({'fiat_balance_margin': float(balance['available'])})

    print(Balances)
    
    if leverage == 0:
        if Balances['coin_balance_margin'] > 0.0 and Balances['coin_balance_exchange'] < amount: 
            print(client.wallet_transfer(Balances['coin_balance_margin'], Coin, 'margin', 'exchange'))
            time.sleep(5)
        if Balances['fiat_balance_margin'] > 0.0 and Balances['fiat_balance_exchange'] < amount*price:
            print(client.wallet_transfer(Balances['fiat_balance_margin'], Fiat[0], 'margin', 'exchange'))
            time.sleep(5)
            
    elif leverage != 0:
        if Balances['coin_balance_exchange'] > 0.0 and Balances['coin_balance_margin'] < amount: 
            print(client.wallet_transfer(Balances['coin_balance_exchange'], Coin, 'exchange', 'margin'))
            time.sleep(5)
        if Balances['fiat_balance_exchange'] > 0.0 and Balances['fiat_balance_margin'] < amount*price:
            print(client.wallet_transfer(Balances['fiat_balance_exchange'], Fiat[0], 'exchange', 'margin'))
            time.sleep(5)           
    
#print(Bitfinex_Wallet_Transfer('BTC', 0.02, 10000, 0)
    
#def Bitfinex_Wallet_Transfer():
#    
#    client = Bitfinex_Private_Client()
#
#    return client.wallet_transfer(50.00, 'EUR', 'exchange', 'margin')
    
#print(Bitfinex_Wallet_Transfer()
    
def Bitfinex_Balances(Coin):
    
    balances = Bitfinex_Private_Client().get_balances()
        
    coin_balance = 0.0
    for balance in balances:
        if balance['currency'] == Coin.lower() and balance['type'] == 'exchange':
            coin_balance += float(balance['available'])
        if balance['currency'] == Coin.lower() and balance['type'] == 'trading':
            coin_balance += float(balance['available'])
            
    fiat_balance = 0.0
    for balance in balances:
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'exchange':
            fiat_balance += float(balance['available'])
        if balance['currency'] == Fiat[0].lower() and balance['type'] == 'trading':
            fiat_balance += float(balance['available'])
    
    return {Coin: coin_balance, Fiat[0]: fiat_balance}

#print(Bitfinex_Balances('BTC')
    
    
def Bitfinex_Limit_Order(Coin, amount, side, price, leverage):
    
    Bitfinex_Wallet_Transfer(Coin, amount, price, leverage)
            
#    pair = Coin.lower() + Fiat[0].lower()    
    
#    Order = Bitfinex_Private_Client().limit_order(str(pair), str(amount),
#                                                  str(side), str(price))  

#    print('Message from Bitstamp: ' + str(Order)
#    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
#    return Order
    
#print(Bitfinex_Limit_Order('BTC', 0.002, 'buy', 8000.0)
    
def Bitfinex_Market_Order(Coin, amount, side, leverage):
    
    Bitfinex_Wallet_Transfer(Coin, amount, leverage)
    
    pair = Coin.lower(), Fiat[0].lower()    
    Order = Bitfinex_Private_Client().market_order(str(amount), str(side), pair[0], pair[1])  

#    print('Message from Bitstamp: ' + str(Order)
#    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order
    
def Bitfinex_Check_Order(ref):
    
    Order = Bitfinex_Private_Client().order_status(ref)
    
#    print('Message from Bitstamp: ' + str(Order)
#    log.write('\nMessage from Bitstamp: ' + str(Order)) 
    
    return Order

#print(Bitfinex_Check_Order(7147701799L)

def Bitfinex_Filled(Order):
    
    Order_ID = Order['ID']
    
    isFilled = float(Bitfinex_Check_Order(Order_ID)['remaining_amount'])
    
    if  isFilled == 0.0:
        Filled = True
    else: Filled = False
    
    return Filled
    
#print(Bitfinex_Filled({'ID': 7147701799L})

    
def Bitfinex_Cancel_Order(ref):
    
    Bitfinex_Private_Client().cancel_order(ref)
    
    time.sleep(5)    

#    print('Message from Bitstamp: ' + str(Order)
#    log.write('\nMessage from Bitstamp: ' + str(Order))

    cancelled = Bitfinex_Check_Order(ref)['is_cancelled']
    
    return cancelled
    
#print(Bitfinex_Cancel_Order(7147923915L)
    

print(Bitfinex_Orderbook('BTC'))