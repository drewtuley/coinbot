import time


def convert_epoch(epoch):
    t_date = time.localtime(epoch)
    return time.strftime('%b %d, %Y %H:%M:%S', t_date)


def convert_epoch_norm(epoch):
    t_date = time.localtime(epoch)
    return time.strftime('%Y-%m-%d %H:%M:%S', t_date)
