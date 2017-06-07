import os
import sys
import time


if len(sys.argv) > 1:
    f = sys.argv[1]
    atime = os.stat(f).st_atime
    while True:
        s = os.stat(f)
        if s.st_atime != atime:
            atime = os.stat(f).st_atime
            print(s)
        time.sleep(1)


