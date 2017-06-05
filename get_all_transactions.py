import sys

from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    period = 'hour'
    if len(sys.argv) > 1:
        period = str(sys.argv[1])

    txns = cb.get_transactions(time_value=period)
    for txn in txns:
        print(txn)
