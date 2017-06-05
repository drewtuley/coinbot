from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    balance = cb.get_balance()
    print('My Balance: \n{}'.format(balance))


    open_orders = cb.get_open_orders()
    print('My Open Orders:')
    for open_order in open_orders:
        print(open_order)


    print ('My Transactions (top 10)')
    user_txns = cb.get_user_transactions()
    for txn in user_txns[:10]:
        print(txn)
