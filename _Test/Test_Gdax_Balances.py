import GDAX
import Keys


    
key = Keys.GDAX()
    
client = GDAX.AuthenticatedClient(key['key'],key['secret'],key['passphrase'])
accounts = client.getAccounts()

print accounts

#for account in accounts:
#    if account['currency'] == 'EUR':
#        eur = round(float(account['balance']),2)  
#
#for account in accounts:
#    if account['currency'] == 'BTC':
#        btc = round(float(account['balance']),8)
        
