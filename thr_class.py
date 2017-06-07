import threading
import time


class Me(object):
    def __init__(self):
        self.val = 1

    def inc(self):
        self.val += 1

    def __repr__(self):
        return '{}'.format(self.val)

    def auto_inc(self, interval):
        print('in auto inc')
        while True:
            self.val += 1
            time.sleep(interval)


    def start(self, interval):
        t = threading.Thread(target = self.auto_inc, args=(interval,))
        t.start()

m = Me()
print (m)
m.inc()
print (m)

m.start(0.5)
while True:
    print(m)
    time.sleep(1)
