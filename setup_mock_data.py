import sqlite3
from datetime import datetime
from datetime import timedelta
import random



if __name__ == "__main__":
    schema = 'coinfloor.mock.sql'
    db_filename = 'data/coinfloor.mock.db'

    with sqlite3.connect(db_filename) as conn:
        with open(schema) as f:
            schema = f.read()
            conn.executescript(schema)


        # create transactions
        txns_to_add = 2000
        tid = 11234321
        dt = datetime.now() - timedelta(minutes=txns_to_add*5)
        price = 1000
        amount = 0.1
        for x in range(0,txns_to_add):
            price = price + ((random.random()*10)-5)
            amount = 1.0
            sql = 'insert into txn_transaction (tf_date, tid, price, amount) values ("{}", "{}", {:4.2f}, {});'.format(tid, str(dt), price, amount)
            print(sql)
            conn.execute(sql)
            tid += 1
            dt = dt + timedelta(minutes=5)
        crsr = conn.execute('select count(*) from txn_transaction;')
        for row in crsr.fetchall():
            count, = row
            print('inserted {} rows to txn_transaction'.format(count))
        
