import time

Attempts = 4

for attempt in range(1, Attempts):
    print 'Attempt: %s' % attempt
    if attempt < Attempts-1:
        for i in range(1, 5):
            time.sleep(1)
            print 'Sleeping for %s S' %i*1