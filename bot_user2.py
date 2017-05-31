from CoinfloorBot import CoinfloorBot
import time

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    loops = 10
    while loops > 0:
        bids, asks = cb.get_order_book()
        print ('Got {} bids, {} asks'.format(len(bids), len(asks)))
        # display top 10 bids/asks
        for ix in range(0, 10):
            print('bid: {bid:30} ask: {ask:30}'.format(bid=bids[ix].show(), ask=asks[ix].show()))
        time.sleep(.1)
        loops -= 1
