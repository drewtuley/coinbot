from CoinfloorBot import CoinfloorBot
import time

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    loops = 10
    while loops > 0:
        t = cb.get_ticker()
        print(t)
        cb.post_to_slack(str(t))
        time.sleep(1)
        loops -= 1
