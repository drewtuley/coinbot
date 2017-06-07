from flask import Flask
from flask import request
import json
from CoinfloorBot import Ticker
from CoinfloorBot import Balance


class CoinfloorServer(Flask):
    def set_stuff(self, x):
        self.x = x


app = CoinfloorServer(__name__)

@app.route('/bist/<fromccy>/<toccy>/ticker/', methods=['GET'])
def ticker(fromccy, toccy):
    t = Ticker()
    t.last = 2101.1
    t.high = 2200.0
    t.low = 2000.0
    t.vwap = 1900.11
    t.volume = 150
    t.ask = 2103.1
    t.bid = 2009.4
    return t.to_json()


@app.route('/bist/<fromccy>/<toccy>/order_book/', methods=['GET'])
def order_book(fromccy, toccy):
    return json.dumps({'bids': [], 'asks': []})


@app.route('/bist/<fromccy>/<toccy>/transactions/', methods=['GET'])
def transactions(fromccy, toccy):
    return json.dumps({})


@app.route('/bist/<fromccy>/<toccy>/balance/', methods=['GET', 'POST'])
def balance(fromccy, toccy):
    b = Balance()
    b.gbp_available = 1000.0
    b.gbp_balance = 1000.0
    b.gbp_reserved = 0.0
    b.xbt_available = 0.0
    b.xbt_balance = 0.0
    b.xbt_reserved = 0.0
    return b.to_json()


if __name__ == "__main__":
    app.run(debug=True)

