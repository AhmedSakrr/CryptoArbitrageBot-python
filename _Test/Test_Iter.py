import itertools


#exchanges = ['Kraken', 'Bitstamp', 'Gdax', 'Bl3p', 'TheRock', 'Cex', 'Wex', 'BitBay', 'Quoinex']
#
Coins = ['BTC', 'LTC', 'ETH']
#    
#Exchange_Iterations = list(itertools.permutations(exchanges, 2))
#
#Permuatations = list(itertools.product(Exchange_Iterations, Coins))
#
#
##Permuatations = [dict(zip(('Long', 'Short'), i)) for i in Permuatations if i[1]['Shorting'] is True]
#
#print Permuatations

print map('Coin', Coins)