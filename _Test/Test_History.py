
import time
import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.finance import candlestick_ohlc

#constants
pair1 = 'BTC', 'XBT'
pair2 = 'EUR'


import krakenex

_1min, _5min, _15min, _30min, _1hour, _4hour, _1day, _1week, _2week = (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)

interval = _1day # change to desired timeframe
since = True
since_date = '2016-12-31 00:00:00'

date = time.mktime(time.strptime(since_date, '%Y-%m-%d %H:%M:%S'))
    
pair = 'X'+pair1[1]+'Z'+pair2

params = {'pair': pair,
          'interval': interval,
          'since': date if since is True else ''} # If since is False plots max amount of 720 points

history = krakenex.API().query_public('OHLC', params)['result'][pair]

history = [[float(i) for i in j] for j in history]


time, openp, highp, lowp, closep, vwap, volume, count = zip(*history)

#time = [int(i) for i in time]



x = 0
y = len(time)
ohlc = []

while x < y:
    append_me = time[x], openp[x], highp[x], lowp[x], closep[x], volume[x]
    ohlc.append(append_me)
    x+=1

plt.figure('Fig-1')
ax1 = plt.subplot2grid((1,1),(0,0))

candlestick_ohlc(ax1, ohlc)
#plt.axes().xaxis_date()
#plt.axes().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))

#for label in ax1.xaxis.get_ticklabels():
#    label.set_rotation(45)
plt.title('Kraken')
plt.xlabel('Time')
plt.ylabel('Price')

time = [datetime.datetime.fromtimestamp(i) for i in time]

plt.figure('Fig-2')
plt.plot(time, closep)
plt.title('Kraken')
plt.xlabel('Time')
plt.ylabel('Price')

#ax1 = plt.subplot2grid((1,1),(0,0))

plt.axes().xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
#start, end = ax1.get_xlim()
#ax1.xaxis.set_ticks(np.arange(start, end, 1))
plt.xticks(rotation=45)
    
plt.show()
















