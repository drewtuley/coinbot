import ConfigParser
import json

import requests

base_private_url = 'https://webapi.coinfloor.co.uk:8090/bist/{fromccy}/{toccy}/{op}/'


def build_url(fromccy, toccy, op):
    return base_private_url.format(fromccy=fromccy, toccy=toccy, op=op)


if __name__ == "__main__":
    fromccy = 'XBT'
    toccy = 'GBP'
    op = 'balance'

    config = ConfigParser.SafeConfigParser()
    config.read('coinfloor.props')

    user = config.get('user', 'userid')
    password = config.get('user', 'password')

    get_balance = base_private_url.format(fromccy=fromccy, toccy=toccy, op=op)
    # print(get_balance)
    s = requests.Session()
    s.auth = (user, password)
    resp = s.get(get_balance)
    if resp.status_code == 200:
        print json.dumps(resp.json(), indent=2)

    op = 'user_transactions'
    user_txns = base_private_url.format(fromccy=fromccy, toccy=toccy, op=op)
    # s = requests.Session()
    # s.auth = (user, password)
    resp = s.get(user_txns)
    if resp.status_code == 200:
        # print json.dumps(resp.json(), indent=2)
        for txn in resp.json():
            print json.dumps(txn, indent=2)
    else:
        print(resp.status_code)

    op = 'open_orders'
    user_txns = base_private_url.format(fromccy=fromccy, toccy=toccy, op=op)
    # s = requests.Session()
    # s.auth = (user, password)
    resp = s.get(user_txns)
    if resp.status_code == 200:
        print('open orders:')
        # print json.dumps(resp.json(), indent=2)
        for txn in resp.json():
            print json.dumps(txn, indent=2)
    else:
        print(resp.status_code)
