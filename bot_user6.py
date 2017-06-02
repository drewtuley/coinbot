from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    t = cb.get_ticker()
    print(t)

    bal = cb.get_balance()
    print(bal)

    mo, resp = cb.estimate_market('buy', {'total': t.bid/2})
    if mo is not None:
        print('market buy:  {}'.format(mo))
    else:
        print('unable to get estimate buy market: status: {} value {}'.format(resp.status_code, resp.value))

    mo, resp = cb.estimate_market('sell', {'total': t.ask/2})
    if mo is not None:
        print('market sell: {}'.format(mo))
    else:
        print('unable to get estimate sell market: status: {} value {}'.format(resp.status_code, resp.value))
