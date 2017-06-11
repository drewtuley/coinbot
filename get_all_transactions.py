import sys

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Transaction

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    period = 'hour'
    if len(sys.argv) > 1:
        period = str(sys.argv[1])

    txns = cb.get_transactions(time_value=period)
    for txn in txns:
        print(txn)

    session = cb.get_db_session()
    for txn in sorted(txns, key = lambda Transaction: Transaction.tid):
        txn_exists = session.query(Transaction).filter(Transaction.tid == txn.tid).first()
        if txn_exists is None:
            session.add(txn)
    session.commit()
