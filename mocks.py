from CoinfloorBot import CoinfloorBot
import time


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.mock.props')

    t = cb.get_ticker()
    print(t)
     

    ob = cb.get_order_book()
    print(ob)

    txns = cb.get_transactions()
    print(txns)

    balance = cb.get_balance()
    print(balance)
