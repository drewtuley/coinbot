import sys

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import UserTransaction

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)

    cb_bch = CoinfloorBot(fromccy='BCH')
    cb_bch.set_config('coinfloor.props')

    tick = cb.get_ticker()
    print('{}'.format(tick))

    bch_tick = cb_bch.get_ticker()
    print('{}'.format(bch_tick))


    gbp_balance, xbt_balance = cb.get_balance()
    gbp_balance, bch_balance = cb_bch.get_balance()
    print('{}'.format(gbp_balance))
    print('{}'.format(xbt_balance))
    print('{}'.format(bch_balance))
    session.add(gbp_balance)  # update to db
    session.add(xbt_balance)  # update to db
    session.add(bch_balance)  # update to db
    session.commit()


    current_price = {}

    xbt_valuation = None
    bch_valuation = None
    if xbt_balance.available > 0:
        mo, resp = cb.estimate_market('sell', {'quantity': xbt_balance.available})
        if mo is not None:
            print('XBT GBP cash valuation: {} @ {:8.2f}'.format(mo, mo.price()))
            xbt_valuation = mo.total
            current_price['XBT'] = mo.price()
        else:
            print('unable to get estimate sell market: status: {} value {}'.format(resp.status_code, resp.value))

    if bch_balance.available > 0:
        mo, resp = cb_bch.estimate_market('sell', {'quantity': bch_balance.available})
        if mo is not None:
            print('BCH GBP cash valuation: {} @ {:8.2f}'.format(mo, mo.price()))
            bch_valuation = mo.total
            current_price['BCH'] = mo.price()
        else:
            print('unable to get estimate sell market: status: {} value {}'.format(resp.status_code, resp.value))

    print('Total Cash Valuation:           {:,.2f}'.format(xbt_valuation + bch_valuation + gbp_balance.balance))

    open_orders = cb.get_open_orders()
    print('\nMy Open Orders:')
    for open_order in open_orders:
        print(open_order)


    txns_to_show = 10
    if len(sys.argv) > 1:
        txns_to_show = int(sys.argv[1])

    user_txns = cb.get_user_transactions()
    for txn in sorted(user_txns, key=lambda UserTransaction: UserTransaction.tid):
        txn_exists = session.query(UserTransaction).filter_by(tid=txn.tid).first()
        if txn_exists is None:
            session.add(txn)
    user_txns = cb_bch.get_user_transactions()
    for txn in sorted(user_txns, key=lambda UserTransaction: UserTransaction.tid):
        txn_exists = session.query(UserTransaction).filter_by(tid=txn.tid).first()
        if txn_exists is None:
            session.add(txn)

    session.commit()

    print ('My Transactions (top {})'.format(txns_to_show))
    db_user_txns = session.query(UserTransaction).order_by(UserTransaction.tf_date.desc())
    run_tot = 0.0
    for txn in db_user_txns[:txns_to_show]:
        if current_price[txn.fromccy] is not None and txn.gbp_amount < 0:
            val = current_price[txn.fromccy] * txn.fromccy_amount
            pnl = val + txn.gbp_amount
        else:
            val = 0.0
            pnl = 0.0
        run_tot += pnl
        print('{txn} Val:{val:10.2f} PnL:{pnl:10.2f} ({rt:10.2f})'.format(txn=txn, val=val, pnl=pnl, rt=run_tot))

