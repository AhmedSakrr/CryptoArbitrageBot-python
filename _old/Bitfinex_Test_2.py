import Bitfinex_API

Bitfinex_Key = 'p5y9n7U76OLurdzA9CvHPEaMw5GPQL24OrvRvCr7UfW'
Bitfinex_Secret = 'fHd8fGHsKaCPDUnjZiVkIwBCJD7nFqbxbyrlRvosXXH'

pair1 = 'BTC'
pair2 = 'USD'

Exchanges = ['Kraken', 'Bitstamp', 'GDAX', 'Bitonic-BL3P', 'XBTCE', 'TheRock', 'CEXIO', 'coinmate', 'BTC-E']

def main():
    
    Exchange_A = Bitfinex_Exchange(Bitfinex_Key,Bitfinex_Secret)
    
    Exchange_A_Balance = Exchange_A.balance()
    
    Exchange_A_Fees = 
    
    Exchange_A_Buy = Exchange_A.prices(pair1, pair2)['buy']
    Exchange_A_Sell = Exchange_A.prices(pair1, pair2)['sell']
    
    print Exchange_A_Buy
    print Exchange_A_Sell
        
class Bitfinex_Exchange:
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.Private = Bitfinex_API.TradeClient(self.key, self.secret)
        pass
    
    def balance(self):
        balance = [10]# self.Private.balances()
        print "Bitfinex"
        print "Balance = ", balance[0]
        
        if not balance:
            print "You've got no money!"
        else:
            return balance[0]        
    
    def prices(self,pair1,pair2):
        self.pair1 = pair1
        self.pair2 = pair2        
        
        Buy = Bitfinex_API.Client().ticker(self.pair1+self.pair2)['ask']
        Sell = Bitfinex_API.Client().ticker(self.pair1+self.pair2)['bid']
        
        Prices = {"buy": Buy, "sell": Sell}        
        
#        print "Price ", Prices        
        return Prices

    def fees(self):
        
        fees = self.Private.account_infos()
           
        open_fee, close_fee = fees[0]['taker_fees'], fees[0]['maker_fees'] 
        
        print 'Fee to open is', open_fee, '%\n', 'Fee to close is', close_fee, '%'        
        return {"buy_fee":open_fee, "sell_fee": close_fee}

    def send_order(self, amount, price, side, pair):
        self.amount = amount        
        self.price = price
        self.side = side
        self.pair = pair   
       
        order_amount = '{0:f}'.format(self.amount)
        order_price = '{0:f}'.format(self.price)         
               
        print self.Private.place_order(order_amount, order_price, self.side, 'market', self.pair)
        print "Order Sent"   

if __name__ == '__main__':
    main()