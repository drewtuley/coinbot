from CoinfloorBot import CoinfloorBot
import time


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.mock.props')

    t = cb.get_ticker()
    print(t)
     
