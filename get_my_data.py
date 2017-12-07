import sys

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import UserTransaction

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)

    tick = cb.get_ticker()
    print(tick)

    current_xbt_price = None

    balance = cb.get_balance()
    print('My Balance: \n{}'.format(balance))
    session.add(balance)  # update to db
    session.commit()

    if balance.xbt_available > 0:
        mo, resp = cb.estimate_market('sell', {'quantity': balance.xbt_available})
        if mo is not None:
            print('GBP cash valuation: {} @ {}'.format(mo, mo.price()))
            print('Total Cash Valuation: {:,.2f}'.format(mo.total + balance.gbp_balance))
            current_xbt_price = mo.price()
        else:
            print('unable to get estimate sell market: status: {} value {}'.format(resp.status_code, resp.value))

    open_orders = cb.get_open_orders()
    print('My Open Orders:')
    for open_order in open_orders:
        print(open_order)

    txns_to_show = 10
    if len(sys.argv) > 1:
        txns_to_show = int(sys.argv[1])

    print ('My Transactions (top {})'.format(txns_to_show))
    user_txns = cb.get_user_transactions()
    for txn in sorted(user_txns, key=lambda UserTransaction: UserTransaction.tid):
        txn_exists = session.query(UserTransaction).filter_by(tid=txn.tid).first()
        if txn_exists is None:
            session.add(txn)

    session.commit()

    gbp_balance = balance.gbp_balance
    xbt_balance = balance.xbt_balance
    db_user_txns = session.query(UserTransaction).order_by(UserTransaction.tid.desc())
    run_tot = 0.0
    for txn in db_user_txns[:txns_to_show]:
        if current_xbt_price is not None:
            val = current_xbt_price * txn.xbt
            pnl = val + txn.gbp
        else:
            val = 0.0
            pnl = 0.0
        run_tot += pnl
        print('{txn} Val:{val:10.2f} PnL:{pnl:10.2f} ({rt:10.2f})'.format(txn=txn, val=val, pnl=pnl, rt=run_tot))

    # our_txn = session.query(UserTransaction).filter_by(tid='1496828041313320').first()  # doctest:+NORMALIZE_WHITESPACE
    # print(our_txn)
