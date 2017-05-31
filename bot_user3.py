from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    txns = cb.get_transactions(time_value='hour')
    for txn in txns:
        print(txn.show())

