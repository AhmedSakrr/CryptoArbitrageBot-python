import pandas as pd
import time
import datetime 

current_time = datetime.datetime.now()

test_time = datetime.datetime.now()


for Exchange in Exchanges:
    Exchange.update({'Time': current_time})
    Exchange_DF = pd.DataFrame(data = [current_time, Exchange['Prices']])
    test = pd.DataFrame({'Time': test_time, 'Prices': Exchange['Prices'] })

    Exchange_DF.to_pickle(str(Exchange['Name'])+'.pkl')
#    
#    
#Kraken1 = pd.load('Kraken.pkl')

#for Exchange in Exchanges:
#    Exchange.update({'Time': new_time})
#    Exchange_DF = pd.DataFrame(Exchange)
#    Exchange_DF.to_pickle(str(Exchange['Name'])+'.pkl')
#
#    
#Kraken2 = pd.load('Kraken.pkl')
#
#Kraken = Kraken1.append(Kraken2)


