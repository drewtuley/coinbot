import time


def convert_epoch(epoch):
    t_date = time.localtime(epoch)
    return time.strftime('%b %d, %Y %H:%M:%S', t_date)
