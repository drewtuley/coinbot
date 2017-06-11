import sys

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import UserTransaction

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    balance = cb.get_balance()
    print('My Balance: \n{}'.format(balance))

    open_orders = cb.get_open_orders()
    print('My Open Orders:')
    for open_order in open_orders:
        print(open_order)

    txns_to_show = 10
    if len(sys.argv) > 1:
        txns_to_show = int(sys.argv[1])

    print ('My Transactions (top {})'.format(txns_to_show))
    user_txns = cb.get_user_transactions()
    gbp_balance = balance.gbp_balance
    xbt_balance = balance.xbt_balance
    for txn in user_txns[:txns_to_show]:
        gbp_balance -= txn.gbp
        xbt_balance -= txn.xbt
        print('{txn} GBP: {gbp:10.2f} XBT: {xbt:8.4f}'.format(txn=txn, gbp=gbp_balance, xbt=xbt_balance))

    session = cb.get_db_session(echo=False)
    for txn in sorted(user_txns, key=lambda UserTransaction: UserTransaction.tid):
        txn_exists = session.query(UserTransaction).filter_by(tid=txn.tid).first()
        if txn_exists is None:
            session.add(txn)

    session.commit()

    session.add(balance)
    print(session.new)
    session.commit()

    our_txn = session.query(UserTransaction).filter_by(tid='1496828041313320').first()  # doctest:+NORMALIZE_WHITESPACE
    print(our_txn)
