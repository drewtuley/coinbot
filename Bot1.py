import requests

import utils

if __name__ == "__main__":
    base_public_url = 'https://webapi.coinfloor.co.uk:8090/bist/{fromccy}/{toccy}/{op}/'
    fromccy = 'XBT'
    toccy = 'GBP'
    op = 'ticker'
    geturl = base_public_url.format(fromccy=fromccy, toccy=toccy, op=op)
    resp = requests.get(geturl)
    if resp.status_code == 200:
        print(resp.headers['date'])
        json = resp.json()
        print('high: {high} low: {low}'.
              format(high=json['high'], low=json['low']))
        print ('vwap: {vwap}, volume: {volume}'.format(vwap=json['vwap'], volume=json['volume']))
        print ('last: {last} bid: {bid} ask: {ask}'.format(last=json['last'], bid=json['bid'], ask=json['ask']))

    op = 'order_book'
    geturl = base_public_url.format(fromccy=fromccy, toccy=toccy, op=op)
    resp = requests.get(geturl)
    if resp.status_code == 200:
        print(resp.headers['date'])
        json = resp.json()
        if 'bids' in json:
            for bid in json['bids']:
                print('bids: price: {} amount: {}'.format(bid[0], bid[1]))
        if 'asks' in json:
            for ask in json['asks']:
                print('asks: price: {} amount: {}'.format(ask[0], ask[1]))

    op = 'transactions'
    geturl = (base_public_url + '?time={time}').format(fromccy=fromccy, toccy=toccy, op=op, time='minute')
    # print(geturl)
    resp = requests.get(geturl)
    if resp.status_code == 200:
        print(resp.headers['date'])
        json = resp.json()
        for txn in json:
            tf_date = utils.convert_epoch(int(txn['date']))
            t_id = txn['tid']
            t_price = txn['price']
            t_amount = txn['amount']
            print('Date: {} TxId: {} Price: {} Amount: {}'.format(tf_date, t_id, t_price, t_amount))
    else:
        print('oops:' + resp)
