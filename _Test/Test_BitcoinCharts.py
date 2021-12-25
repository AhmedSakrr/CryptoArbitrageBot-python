import csv
import requests
from matplotlib import dates as mdates
import matplotlib.pyplot as plt
import datetime

exchanges = ('btce', 'rock')
pair1 = 'EUR'

def Extract(exchanges):
    
    trades = []
    
    for exchange in exchanges:        
    
        URL = 'http://api.bitcoincharts.com/v1/trades.csv?symbol='+exchange+pair1    
        s = requests.Session()            
        download = s.get(URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        trades.append(list(cr))
        
    return trades

data = Extract(exchanges)

data = [i[-10000:] for i in data]

data = [[[float(i) for i in j] for j in k] for k in data]

start_time = [datetime.datetime.fromtimestamp(i[0][0]) for i in data]
end_time = [datetime.datetime.fromtimestamp(i[-1][0]) for i in data]



        
plt.figure(1)
ax = plt.subplot(111)

x0 = [i[0] for i in data[0]]
x0 = [datetime.datetime.fromtimestamp(i) for i in x0]
x1 = [i[0] for i in data[1]]
x1 = [datetime.datetime.fromtimestamp(i) for i in x1]

y0 =[i[1] for i in data[0]]
y1 =[i[1] for i in data[1]]

plt.plot(x0, y0, label=(exchanges[0]))
plt.plot(x1, y1, label=(exchanges[1]))
ax.legend()

plt.axes().xaxis.set_major_formatter(mdates.DateFormatter("%d/%m %H:%M"))

plt.xlabel('Time')
plt.xticks(rotation=30)
plt.ylabel('Price (%s)' % pair1)

plt.show






