from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    open_orders = cb.get_open_orders()
    for open_order in open_orders:
        print(open_order.show())
