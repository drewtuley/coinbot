from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Transaction

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')


    session = cb.get_db_session()
    all_txns = session.query(Transaction).all()
    for txn in all_txns:
        print(txn)
