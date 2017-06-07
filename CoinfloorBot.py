from __future__ import print_function

import ConfigParser
import json

import requests

import utils


class UserTransaction:
    txn_type_map = {0: 'deposit', 1: 'withdrawal', 2: 'market trade'}

    def __init__(self):
        self.tf_date = None
        self.tid = None
        self.raw_type = None
        self.mapped_type = None
        self.gbp = 0.0
        self.xbt = 0.0
        self.xbt_gbp = 0.0
        self.fee = 0.0
        self.order_id = None

    def parse(self, txn):
        self.tf_date = str(txn['datetime'])
        self.tid = int(txn['id'])
        self.raw_type = int(txn['type'])
        self.mapped_type = self.txn_type_map[self.raw_type]
        self.gbp = float(txn['gbp'])
        self.xbt = float(txn['xbt'])
        try:
            self.xbt_gbp = float(txn['xbt_gbp'])
            self.order_id = str(txn['order_id'])
        except TypeError:
            pass
        self.fee = float(txn['fee'])

    def to_json(self):
        return json.dumps({'datetime': self.tf_date, 'id': self.tid, 'type': self.raw_type,
                           'gbp': self.gbp, 'xbt': self.xbt, 'xbt_gbp': self.xbt_gbp, 'order_id': self.order_id,
                           'fee': self.fee})

    def __repr__(self):
        return 'date: {} type: {:15} GBP: {:10.2f}  XBT: {:10.4f} @ {:7.2f}  - id {:18}'.format(self.tf_date,
                                                                                                self.mapped_type,
                                                                                                self.gbp, self.xbt,
                                                                                                self.xbt_gbp,
                                                                                                self.tid)


class Transaction:
    def __init__(self):
        self.tf_date = None
        self.tid = None
        self.price = None
        self.amount = None

    def get_value(self):
        return self.price * self.amount

    def parse(self, txn):
        self.amount = float(txn['amount'])
        self.price = float(txn['price'])
        self.tid = int(txn['tid'])
        self.tf_date = utils.convert_epoch(int(txn['date']))

    def to_json(self):
        return json.dumps({'amount': self.amount, 'price': self.price, 'tid': self.tid, 'date': self.tf_date})

    def __repr__(self):
        return '{date} amount: {amount:10} price: {price} (value: {value:10}) ' \
               'tid: {tid}'.format(date=self.tf_date,
                                   amount=self.amount,
                                   price=self.price,
                                   value=self.get_value(),
                                   tid=self.tid)


class Order:
    def __init__(self):
        self.price = None
        self.amount = None

    def total(self):
        return float(self.price * self.amount)

    def parse(self, order):
        self.price = float(order[0])
        self.amount = float(order[1])

    def to_json(self):
        return json.dumps([self.price, self.amount])

    def __repr__(self):
        return 'price: {price} amount: {amount}'.format(price=self.price, amount=self.amount)

    def asmap(self):
        return {'price': self.price, 'amount': self.amount}


class OpenOrder(Order):
    order_type_map = {0: 'buy', 1: 'sell'}

    def __init__(self):
        Order.__init__(self)
        self.type = None
        self.id = None
        self.order_date = None

    def parse(self, order):
        Order.parse(self, [order['price'], order['amount']])
        self.raw_type = order['type']
        self.type = self.order_type_map[self.raw_type]
        self.id = int(order['id'])
        self.order_date = str(order['datetime'])

    def get_id(self):
        return self.id

    def to_json(self):
        return json.dumps({'type': self.raw_type, 'id': self.id,
                           'datetime': self.order_date, 'price': self.price, 'amount': self.amount})

    def __repr__(self):
        return 'date: {date} {type:4} - price: {price} ' \
               'amount: {amount} total: {total} ({id})'.format(price=self.price,
                                                               amount=self.amount,
                                                               type=self.type,
                                                               id=self.id,
                                                               date=self.order_date,
                                                               total=self.total())


class Balance:
    def __init__(self):
        self.gbp_balance = None
        self.gbp_available = None
        self.gbp_reserved = None
        self.xbt_balance = None
        self.xbt_available = None
        self.xbt_reserved = None

    def parse(self, balance):
        self.gbp_available = float(balance['gbp_available'])
        self.gbp_balance = float(balance['gbp_balance'])
        self.gbp_reserved = float(balance['gbp_reserved'])
        self.xbt_available = float(balance['xbt_available'])
        self.xbt_balance = float(balance['xbt_balance'])
        self.xbt_reserved = float(balance['xbt_reserved'])

    def to_json(self):
        return json.dumps(
            {'gbp_available': self.gbp_available, 'gbp_balance': self.gbp_balance, 'gbp_reserved': self.gbp_reserved,
             'xbt_available': self.xbt_available, 'xbt_balance': self.xbt_balance, 'xbt_reserved': self.xbt_reserved})

    def __repr__(self):
        return 'GBP: r {} a {} b {}   XBT: r {} a {} b {}'.format(self.gbp_reserved, self.gbp_available,
                                                                  self.gbp_balance,
                                                                  self.xbt_reserved, self.xbt_available,
                                                                  self.xbt_balance)


class Ticker:
    def __init__(self):
        self.last = None
        self.high = None
        self.low = None
        self.vwap = None
        self.volume = None
        self.bid = None
        self.ask = None
        self.date = None

    def parse(self, resp):
        self.date = resp.headers['date']
        tick = resp.json()
        try:
            self.last = float(tick['last'])
            self.high = float(tick['high'])
            self.low = float(tick['low'])
            self.vwap = float(tick['vwap'])
            self.volume = float(tick['volume'])
            self.ask = float(tick['ask'])
            self.bid = float(tick['bid'])
        except (TypeError, KeyError) as err:
            pass

    def compare(self, other):
        if other is not None and isinstance(other, Ticker):
            return self.last == other.last and \
                   self.high == other.high and self.low == other.low and self.vwap == other.vwap and \
                   self.volume == other.volume and self.ask == other.ask and self.bid == other.bid

    def __repr__(self):
        return ('Ticker: {date} Last: {last} High: {high} Low: {low} vwap: {vwap} volume: {volume} '
                'bid: {bid} ask: {ask}'.
                format(date=self.date, last=self.last, high=self.high,
                       low=self.low, vwap=self.vwap, volume=self.volume, bid=self.bid, ask=self.ask))

    def to_json(self):
        return json.dumps({'last': self.last, 'high': self.high, 'low': self.low, 'vwap': self.vwap,
                           'volume': self.volume, 'bid': self.bid, 'ask': self.ask})


class MarketOrder:
    def __init__(self):
        self.total = None
        self.quantity = None

    def price(self):
        return self.total / self.quantity

    def parse(self, mo):
        self.total = float(mo['total'])
        self.quantity = float(mo['quantity'])

    def to_json(self):
        return json.dumps({'total': self.total, 'quantity': self.quantity})

    def __repr__(self):
        return 'total: {total} quantity: {quantity}'.format(total=self.total, quantity=self.quantity)

    def __eq__(self, other):
        return other is not None and isinstance(other,
                                                MarketOrder) and self.total == other.total and self.quantity == other.quantity


class MarketOrderRemaining(object):
    def __init__(self):
        self.remaining = None

    def parse(self, mor):
        self.remaining = float(mor['remaining'])

    def to_json(self):
        json.dumps({'remaining': self.remaining})

    def __repr__(self):
        return 'remaining: {}'.format(self.remaining)


class Error(object):
    def __init__(self, text):
        self.text = text


class CoinfloorBot:
    def __init__(self):
        self.config_file = None
        self.coinfloor_url = None
        self.fromccy = None
        self.toccy = None
        self.userid = None
        self.password = None
        self.slack_do_post = False
        self.slack_url = None
        self.slack_username = 'coinfloor.poster'

        self.allow_market_order = False

        self.session = None

    def __dir__(self):
        return ['config_file', 'coinfloor_url', 'fromccy', 'toccy', 'userid', 'password', 'slack_do_post', 'slack_url',
                'slack_username',
                'allow_market_order']

    def set_config(self, config_file):
        self.config_file = config_file
        config = ConfigParser.SafeConfigParser()
        config.read(self.config_file)

        try:
            self.coinfloor_url = config.get('coinfloor', 'url')
            self.fromccy = config.get('coinfloor', 'default_fromccy')
            self.toccy = config.get('coinfloor', 'default_toccy')
            self.userid = config.get('user', 'userid')
            self.password = config.get('user', 'password')
            self.slack_url = config.get('slack', 'url')
            self.slack_do_post = bool(config.get('slack', 'do_post') == 'True')

            self.xbt_to_trade = float(config.get('trade', 'xbt_to_trade'))
            self.min_profit_pc = float(config.get('trade', 'min_profit_pc'))
            self.max_loss_pc = float(config.get('trade', 'max_loss_pc'))

            self.allow_market_order = bool(config.get('control', 'allow_market_order') == 'True')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError) as var:
            print(var)

    def set_ccy(self, fromccy, toccy):
        self.fromccy = fromccy
        self.toccy = toccy

    def get_url(self, op):
        return self.coinfloor_url.format(fromccy=self.fromccy, toccy=self.toccy, op=op)

    def get_ticker(self):
        url = self.get_url('ticker')
        t = Ticker()
        r = requests.get(url)
        if r.status_code == 200:
            t.parse(r)
        return t

    def get_order_book(self):
        bids = []
        asks = []
        url = self.get_url('order_book')
        r = requests.get(url)
        if r.status_code == 200:
            obook = r.json()
            if 'bids' in obook:
                for bid in obook['bids']:
                    o = Order()
                    o.parse(bid)
                    bids.append(o)
            if 'asks' in obook:
                for ask in obook['asks']:
                    o = Order()
                    o.parse(ask)
                    asks.append(o)
        return bids, asks

    def get_transactions(self, time_value='minute'):
        url = self.get_url('transactions')
        params = {'time': time_value}
        r = requests.get(url, params=params)
        transactions = []
        if r.status_code == 200:
            for txn in r.json():
                t = Transaction()
                t.parse(txn)
                transactions.append(t)

        return transactions

    def get_session(self):
        if self.session is None:
            self.session = requests.Session()
            self.session.auth = (self.userid, self.password)

        return self.session

    def get_balance(self):
        url = self.get_url('balance')
        s = self.get_session()
        r = s.get(url)
        if r.status_code == 200:
            b = Balance()
            b.parse(r.json())
            return b
        else:
            return None

    def get_open_orders(self):
        """Private user function"""
        url = self.get_url('open_orders')
        open_orders = []
        s = self.get_session()
        r = s.get(url)
        if r.status_code == 200:
            for order in r.json():
                o = OpenOrder()
                o.parse(order)
                open_orders.append(o)

        return open_orders

    def get_user_transactions(self):
        user_txns = []
        url = self.get_url('user_transactions')
        s = self.get_session()
        r = s.get(url)
        if r.status_code == 200:
            for txn in r.json():
                t = UserTransaction()
                t.parse(txn)
                user_txns.append(t)
        return user_txns

    def place_limit_order(self, type, data):
        url = self.get_url(type)

        s = self.get_session()
        r = s.post(url, data=data)
        if r.status_code == 200:
            o = OpenOrder()
            o.parse(r.json())
            return o, r.json()
        else:
            return None, r.json()

    def close_order(self, open_order):
        url = self.get_url('cancel_order')
        s = self.get_session()

        cancel = {'id': open_order.get_id()}
        s.post(url, data=cancel)

    def close_all_orders(self):
        open_orders = self.get_open_orders()
        for order in open_orders:
            print('close open order {}'.format(order))
            self.close_order(order)

    def estimate_market(self, market_operation, param):
        if market_operation not in ['sell', 'buy']:
            raise ValueError('invalid operation "{}"'.format(market_operation))
        url = self.get_url('estimate_{}_market'.format(market_operation))
        mo = MarketOrder()
        s = self.get_session()
        r = s.post(url, data=param)
        if r.status_code == 200:
            mo.parse(r.json())
            return mo, r
        else:
            return None, r

    def allow_market_orders(self):
        self.allow_market_order = True

    def block_market_orders(self):
        self.allow_market_order = False

    def place_market_order(self, market_operation, param):
        if market_operation not in ['sell', 'buy']:
            raise ValueError('invalid operation "{}"'.format(market_operation))
        if self.allow_market_order:
            url = self.get_url('{}_market'.format(market_operation))
            mor = MarketOrderRemaining()
            s = self.get_session()
            r = s.post(url, data=param)
            if r.status_code == 200:
                mor.parse(r.json())
                return mor, r
            else:
                return None, r
        else:
            e = Error('market orders blocked')
            return None, e

    def post_to_slack(self, message, params={}):
        payload = params
        if self.slack_do_post:
            if 'icon_emoji' not in payload:
                payload['icon_emoji'] = ':moneybag:'
            if 'username' not in payload:
                payload['username'] = self.slack_username
            if 'channel' not in payload:
                payload['channel'] = '#coinfloor'
            payload['text'] = message

            r = requests.post(self.slack_url, json.dumps(payload))


if __name__ == '__main__':
    print('test')

    cb = CoinfloorBot()
    try:
        cb.get_url('open_orders')
    except Exception as err:
        print(err)

    cb.set_config('coinfloor.test.props')
    test_url = cb.get_url('open_orders')
    print(test_url)

    cb.estimate_market('xxx', {'qq': 1})
