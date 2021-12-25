#from datetime import datetime
#import time

amount = 1.0

#start = time.time()
#
#print start
#
#time.sleep(5)
#
#end = time.time()
#
#print end
#
#duration = end - start

duration_hrs = 10

duration_s = duration_hrs*3600

print duration_s

no4hours = int(duration_s / 3600 / 4) / 1.0

print no4hours

cost = 0.001 + 0.001*no4hours * amount


print cost





