import ConfigParser
import time

import requests

base_private_url = 'https://webapi.coinfloor.co.uk:8090/bist/{fromccy}/{toccy}/{op}/'

# kill all open orders

if __name__ == "__main__":
    fromccy = 'XBT'
    toccy = 'GBP'
    op = 'balance'

    order_type_map = {0: 'buy', 1: 'sell'}

    config = ConfigParser.SafeConfigParser()
    config.read('coinfloor.props')

    user = config.get('user', 'userid')
    password = config.get('user', 'password')

    s = requests.Session()
    s.auth = (user, password)

    limit_buy = base_private_url.format(fromccy=fromccy, toccy=toccy, op='buy')
    limit_sell = base_private_url.format(fromccy=fromccy, toccy=toccy, op='sell')

    open_orders = base_private_url.format(fromccy=fromccy, toccy=toccy, op='open_orders')
    cancel_order = base_private_url.format(fromccy=fromccy, toccy=toccy, op='cancel_order')

    buy = {'amount': 0.01, 'price': 1500.00}
    order_resp = s.post(limit_buy, data=buy)
    print('order response: {} value {}'.format(order_resp.status_code, order_resp.text))

    sell = {'amount': 0.01, 'price': 2100.00}
    order_resp = s.post(limit_sell, data=sell)
    print('order response: {} value {}'.format(order_resp.status_code, order_resp.text))

    time.sleep(10)

    resp = s.get(open_orders)
    if resp.status_code == 200:
        # print json.dumps(resp.json(), indent=2)
        print ('open orders:')
        for order in resp.json():
            # print json.dumps(txn,indent=2)
            order_id = order['id']
            order_type = order_type_map[order['type']]
            order_price = order['price']
            order_amount = order['amount']
            print('cancel {} for {} @ {} - id: {}'.format(order_type, order_amount, order_price, order_id))

            params = {'id': order_id}
            c_resp = s.post(cancel_order, data=params)
            print('cancel response status: {} value: {}'.format(c_resp.status_code, c_resp.text))
    else:
        print('error: ' + str(resp.status_code))
