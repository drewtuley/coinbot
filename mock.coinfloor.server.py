import json
import time

from flask import Flask
from flask import request

from CoinfloorBot import Balance
from CoinfloorBot import MarketOrder
from CoinfloorBot import Ticker
from CoinfloorBot import Transaction
from CoinfloorBot import UserTransaction


class CoinfloorServer(Flask):
    def __init__(self, name):
        Flask.__init__(self, name)
        b = Balance()
        b.gbp_available = 1000.0
        b.gbp_balance = 1000.0
        b.gbp_reserved = 0.0
        b.xbt_available = 0.0
        b.xbt_balance = 0.0
        b.xbt_reserved = 0.0
        self.balance = b

        t = Ticker()
        t.last = 2101.1
        t.high = 2200.0
        t.low = 2000.0
        t.vwap = 1900.11
        t.volume = 150
        t.ask = 1989.0
        t.bid = 1992.0
        self.ticker = t

        self.user_transactions = []
        ut_buy = UserTransaction()
        ut_buy.tid = 1
        ut_buy.raw_type = 2
        ut_buy.mapped_type = 'market_trade'
        ut_buy.gbp = -1000.0
        ut_buy.xbt = 0.5
        ut_buy.xbt_gbp = 2000
        ut_buy.order_id = 1
        self.user_transactions.append(ut_buy.to_json())

        ut_sell = UserTransaction()
        ut_sell.tid = 2
        ut_sell.raw_type = 2
        ut_sell.mapped_type = 'market_trade'
        ut_sell.gbp = 1000.0
        ut_sell.xbt = -0.5
        ut_sell.xbt_gbp = 2000
        ut_sell.order_id = 2
        self.user_transactions.append(ut_sell.to_json())


app = CoinfloorServer(__name__)


@app.route('/bist/<fromccy>/<toccy>/ticker/', methods=['GET'])
def ticker(fromccy, toccy):
    return app.ticker.to_json()


@app.route('/bist/<fromccy>/<toccy>/order_book/', methods=['GET'])
def order_book(fromccy, toccy):
    bids = []
    for x in range(0, 20):
        bids.append([1, 2])
    asks = []
    for x in range(0, 20):
        asks.append([3, 4])
    return json.dumps({'bids': bids, 'asks': asks})


@app.route('/bist/<fromccy>/<toccy>/transactions/', methods=['GET'])
def transactions(fromccy, toccy):
    period = request.args.get('time', 'hour')
    app.logger.info(period)

    txns = []
    t = Transaction()
    t.price = 2010.1
    t.amount = 0.443
    t.tid = 192829182912
    t.tf_date = time.strftime('%s', time.localtime())
    txns.append(t.to_json())

    return '[' + ','.join(txns) + ']'


@app.route('/bist/<fromccy>/<toccy>/balance/', methods=['GET', 'POST'])
def balance(fromccy, toccy):
    return app.balance.to_json()


@app.route('/bist/<fromccy>/<toccy>/user_transactions/', methods=['GET'])
def user_transactions(fromccy, toccy):
    return '[' + ','.join(app.user_transactions) + ']'


@app.route('/bist/<fromccy>/<toccy>/estimate_<type>_market/', methods=['POST'])
def estimate_market(fromccy, toccy, type):
    mo = MarketOrder()
    try:
        quantity = float(request.form['quantity'])
        # amount = float(request.form['amount'])
        if type == 'buy':
            mo.total = app.ticker.ask * quantity
        elif type == 'sell':
            mo.total = app.ticker.bid * quantity
        mo.quantity = quantity
    except KeyError as err:
        pass

    try:
        amount = float(request.form['amount'])
        if type == 'buy':
            mo.quantity = amount / app.ticker.ask
        elif type == 'sell':
            mo.quantity = amount / app.ticker.bid
        mo.total = amount
    except KeyError as err:
        pass

    return mo.to_json()


if __name__ == "__main__":
    app.run(debug=True)
