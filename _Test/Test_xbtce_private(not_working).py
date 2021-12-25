import xBTCe

import Keys

pair1 = 'BTC', 'XBT'
pair2 = 'EUR'

def xBTCe_Balances():
    
#    key = Keys.xBTCe()
    
    client = xBTCe.Client.API()
    
    balances = client.getAccount()
    
    print balances

print xBTCe_Balances()
    
    
    
    

    