Kraken = {'Name': 'Kraken', 'Shorting': True} ##
Bitstamp = {'Name': 'Bitstamp', 'Shorting': False}
Gdax = {'Name': 'Gdax', 'Shorting': False}
Bl3p = {'Name': 'Bl3p', 'Shorting': False}
TheRock = {'Name': 'theRock', 'Shorting': False} # No naked shorts :(
Cex = {'Name': 'Cex', 'Shorting': True}
Wex = {'Name': 'Wex', 'Shorting': False}
BitBay = {'Name': 'BitBay', 'Shorting': False}
Quoinex = {'Name': 'Quoinex', 'Shorting': True}

Coins = ['BTC', 'LTC', 'ETH']
#Coins = ['BTC']
Fiat = ['EUR']

Exchanges = [Kraken, Bitstamp, Gdax, Bl3p, TheRock, Cex, Wex, BitBay, Quoinex]



for Exchange in Exchanges:
    
    Balances = {}

    for Coin in Coins:
        
        Balance = {}
        Balance.update({Coin: 0.0})
        Balance.update({Fiat[0]: 1000.0})
        
        Balances.update(Balance)
        
    Exchange.update({'Balances': Balances})
