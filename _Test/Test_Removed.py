import time

current = time.time()/3600

removed = 1519472874.488/3600

print current - removed

Exchanges = []

for Exchange in data:

    if current - removed > 1:
        Exchange.pop('Remove_Time', 0)
        Exchanges.append(Exchange)