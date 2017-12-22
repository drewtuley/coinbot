from __future__ import print_function

import ConfigParser
import json
from datetime import datetime

import requests
from sqlalchemy import Column, Integer, String, Float, DateTime, Sequence
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import utils

Base = declarative_base()


class UserTransaction(Base):
    __tablename__ = 'ut_user_transaction'

    txn_type_map = {0: 'deposit', 1: 'withdrawal', 2: 'market trade'}

    id = Column(Integer, Sequence('user_transaction_id_seq'), primary_key=True)
    tf_date = Column(DateTime)
    tid = Column(Integer)
    raw_type = Column(Integer)
    mapped_type = Column(String)
    gbp_amount = Column(Float)
    fromccy_amount = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    order_id = Column(Integer)
    fromccy = Column(String)

    def parse(self, txn, fromccy):
        self.tf_date = datetime.strptime(txn['datetime'], '%Y-%m-%d %H:%M:%S')
        self.tid = int(txn['id'])
        self.raw_type = int(txn['type'])
        self.mapped_type = self.txn_type_map[self.raw_type]
        self.gbp_amount = float(txn['gbp'])
        self.fromccy_amount = float(txn[fromccy.lower()])
        try:
            self.price = float(txn[fromccy.lower()+'_gbp'])
            self.order_id = str(txn['order_id'])
        except TypeError:
            pass
        self.fee = float(txn['fee'])
        self.fromccy = fromccy

    def to_json(self):
        return {'datetime': str(self.tf_date), 'id': self.tid, 'type': self.raw_type,
                'gbp': self.gbp, 'xbt': self.xbt, 'xbt_gbp': self.xbt_gbp, 'order_id': self.order_id,
                'fee': self.fee}

    def __repr__(self):
        if self.price is None:
            xchng = '{:7s}'.format(' ')
        else:
            xchng = '{:-8.2f}'.format(self.price)
        return '{} {:15} GBP:{:10.2f}  {}:{:10.4f} @ {} - id {:18}'.format(self.tf_date, self.mapped_type, self.gbp_amount, 
                                                                                           self.fromccy, self.fromccy_amount,
                                                                                           xchng,
                                                                                           self.tid)


class Transaction(Base):
    __tablename__ = 'txn_transaction'

    id = Column(Integer, Sequence('transaction_id_seq'), primary_key=True)
    tf_date = Column(DateTime)
    tid = Column(Integer)
    price = Column(Float)
    amount = Column(Float)

    def get_value(self):
        return self.price * self.amount

    def parse(self, txn):
        self.amount = float(txn['amount'])
        self.price = float(txn['price'])
        self.tid = int(txn['tid'])
        self.tf_date = datetime.strptime(utils.convert_epoch_norm(int(txn['date'])), '%Y-%m-%d %H:%M:%S')

    def to_json(self):
        return {'amount': self.amount, 'price': self.price, 'tid': self.tid, 'date': self.tf_date}

    def __repr__(self):
        return '{date} amount: {amount:10} price: {price} (value: {value:10}) ' \
               'tid: {tid}'.format(date=self.tf_date,
                                   amount=self.amount,
                                   price=self.price,
                                   value=self.get_value(),
                                   tid=self.tid)


class Order(Base):
    __tablename__ = 'ord_order'

    id = Column(Integer, Sequence('order_id_seq'), primary_key=True)
    price = Column(Float)
    amount = Column(Float)

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


class OpenOrder(Base):
    __tablename__ = 'opo_open_order'

    order_type_map = {0: 'buy', 1: 'sell'}

    id = Column(Integer, Sequence('open_order_id_seq'), primary_key=True)
    price = Column(Float)
    amount = Column(Float)
    raw_type = Column(Integer)
    type = Column(String)
    order_id = Column(Integer)
    order_date = Column(DateTime)

    def parse(self, order):
        self.price = order['price']
        self.amount = order['amount']
        self.raw_type = order['type']
        self.type = self.order_type_map[self.raw_type]
        self.order_id = int(order['id'])
        self.order_date = str(order['datetime'])

    def get_id(self):
        return self.id

    def to_json(self):
        return {'type': self.raw_type, 'id': self.order_idid,
                'datetime': self.order_date, 'price': self.price, 'amount': self.amount}

    def __repr__(self):
        return 'date: {date} {type:4} - price: {price} ' \
               'amount: {amount} ({id})'.format(price=self.price,
                                                               amount=self.amount,
                                                               type=self.type,
                                                               id=self.order_id,
                                                               date=self.order_date)


class Balance(Base):
    __tablename__ = 'bal_balance'

    id = Column(Integer, Sequence('balance_id_seq'), primary_key=True)
    bal_date = Column(DateTime)
    ccy = Column(String)
    balance = Column(Float)
    available = Column(Float)
    reserved = Column(Float)

    def parse(self, in_balance, in_ccy, in_date):
        self.ccy = in_ccy
        self.bal_date = in_date
        self.available = float(in_balance[in_ccy.lower()+'_available'])
        self.balance = float(in_balance[in_ccy.lower()+'_balance'])
        self.reserved = float(in_balance[in_ccy.lower()+'_reserved'])

    def __repr__(self):
        return '{ccy}: reserved {r:10.2f} available {a:10.2f} balance {b:10.2f}'.format(r=self.reserved, a=self.available, b=self.balance, ccy = self.ccy)


class Ticker(Base):
    __tablename__ = 'tik_ticker'

    id = Column(Integer, Sequence('ticker_id_seq'), primary_key=True)
    last = Column(Float)
    high = Column(Float)
    low = Column(Float)
    vwap = Column(Float)
    volume = Column(Float)
    bid = Column(Float)
    ask = Column(Float)
    date = Column(DateTime)
    fromccy = Column(String)

    def parse(self, resp):
        #print('debug: {}'.format(resp.json()))
        self.date = datetime.strptime(resp.headers['date'], '%a, %d %b %Y %H:%M:%S %Z')

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

    def set_fromccy(self, fromccy):
        self.fromccy = fromccy

    def compare(self, other):
        if other is not None and isinstance(other, Ticker):
            return self.last == other.last and \
                   self.high == other.high and self.low == other.low and self.vwap == other.vwap and \
                   self.volume == other.volume and self.ask == other.ask and self.bid == other.bid


    def compare_significant(self, other):
        if other is not None and isinstance(other, Ticker):
            return self.last == other.last and \
                   self.ask == other.ask and self.bid == other.bid


    def __repr__(self):
        return ('Ticker: {ccy} {date} Last: {last:10.2f} High: {high:10.2f} Low: {low:10.2f} vwap: {vwap:10.2f} volume: {volume:7.2f} '
                'bid: {bid:10.2f} ask: {ask:10.2f}'.
                format(ccy=self.fromccy, date=self.date, last=self.last, high=self.high,
                       low=self.low, vwap=self.vwap, volume=self.volume, bid=self.bid, ask=self.ask))

    def to_json(self):
        return {'last': self.last, 'high': self.high, 'low': self.low, 'vwap': self.vwap,
                'volume': self.volume, 'bid': self.bid, 'ask': self.ask}


class MarketOrder(Base):
    __tablename__ = 'mor_market_order'

    id = Column(Integer, Sequence('market_order_id_seq'), primary_key=True)
    total = Column(Float)
    quantity = Column(Float)

    def price(self):
        return self.total / self.quantity

    def parse(self, mo):
        self.total = float(mo['total'])
        self.quantity = float(mo['quantity'])

    def to_json(self):
        return {'total': self.total, 'quantity': self.quantity}

    def __repr__(self):
        return 'total: {total:10.2f} quantity: {quantity:4.4f}'.format(total=self.total, quantity=self.quantity)

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
    def __init__(self, **kwargs):
        self.config_file = None
        self.coinfloor_url = None
        if 'fromccy' in kwargs:
            self.fromccy = kwargs['fromccy']
        else:
            self.fromccy = None
        if 'toccy' in kwargs:
            self.toccy = kwargs['toccy']
        else:
            self.toccy = None
        self.userid = None
        self.password = None
        self.slack_do_post = False
        self.slack_url = None
        self.slack_channel = None
        self.slack_username = 'coinfloor.poster'

        self.allow_market_order = False

        self.session = None

    def __dir__(self):
        return ['config_file', 'coinfloor_url', 'fromccy', 'toccy', 'userid', 'password', 'slack_do_post', 'slack_url',
                'slack_channel', 'slack_username', 'allow_market_order']

    def set_config(self, config_file):
        self.config_file = config_file
        config = ConfigParser.SafeConfigParser()
        config.read(self.config_file)

        try:
            self.coinfloor_url = config.get('coinfloor', 'url')
            if self.fromccy == None:
                self.fromccy = config.get('coinfloor', 'default_fromccy')
            if self.toccy == None:
                self.toccy = config.get('coinfloor', 'default_toccy')
            self.userid = config.get('user', 'userid')
            self.password = config.get('user', 'password')
            url = '{}-url'.format(self.fromccy.lower())
            self.slack_url = config.get('slack', url)
            self.slack_channel = '#coinfloor-{}'.format(self.fromccy.lower())
            #print('{} {}'.format(self.slack_url, self.slack_channel))
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
            t.set_fromccy(self.fromccy)  
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
            #print('Balance: {}'.format(r.json()))
            now = datetime.now()
            to_b = Balance()
            to_b.parse(r.json(), self.toccy, now)
            from_b = Balance()
            from_b.parse(r.json(), self.fromccy, now)
            return to_b, from_b
        else:
            return None, None

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
        params = {'limit': 50}
        r = s.get(url, params=params)
        if r.status_code == 200:
            for txn in r.json():
                t = UserTransaction()
                t.parse(txn, self.fromccy)
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
                payload['channel'] = self.slack_channel
            payload['text'] = message

            #print('pts: {} {}'.format(self.slack_url, payload))
            r = requests.post(self.slack_url, json.dumps(payload))
            #print(r)

    def get_db_session(self, echo=True):
        engine = create_engine('sqlite:///coinfloor.db', echo=echo)
        # print(UserTransaction.__table__)
        # print(engine)
        Base.metadata.create_all(engine)

        Session = sessionmaker(bind=engine)
        return Session()


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
