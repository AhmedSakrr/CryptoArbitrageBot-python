import threading
import random

numofThreads = 10
threadlist = []


for in range(numofThreads):
    t = threading.Thread(target = Get_Prices,
                         args = (Exchanges,))
                         
    t.start()
    threadList.append((exchange['Name'], t))