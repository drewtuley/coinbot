import sys

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import UserTransaction
from CoinfloorBot import Ticker
from datetime import timedelta

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)
    ten_mins = timedelta(minutes=10)

    gbp_value = 0.0
    db_user_txns = session.query(UserTransaction).order_by(UserTransaction.tf_date.asc())
    for txn in db_user_txns:
        if txn.mapped_type == 'deposit':
            if txn.xbt != 0:
                print(txn)
                ticker_vals = session.query(Ticker).filter(Ticker.date > txn.tf_date - ten_mins, Ticker.date < txn.tf_date + ten_mins)
                avg_last = 0.0
                x = 0
                for tik in ticker_vals:
                    avg_last += tik.last
                    x += 1
                #print('avg_last:{}'.format(avg_last))
                avg_last /= x
                gbp_value += avg_last * txn.xbt
            elif txn.gbp != 0:
                print(txn)
                gbp_value += txn.gbp
            print(gbp_value)
        elif txn.mapped_type == 'withdrawal':
            if txn.gbp != 0:
                gbp_value += txn.gbp
            print(txn)
            print(gbp_value)
