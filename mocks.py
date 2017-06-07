from CoinfloorBot import CoinfloorBot

if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.mock.props')

    t = cb.get_ticker()
    print(t)

    bids, asks = cb.get_order_book()
    print ('Got {} bids, {} asks'.format(len(bids), len(asks)))
    # display top 10 bids/asks
    for ix in range(0, 10):
        print('bid: {bid:30} ask: {ask:30}'.format(bid=bids[ix], ask=asks[ix]))

    txns = cb.get_transactions()
    print(txns)

    balance = cb.get_balance()
    print(balance)

    xbt_to_trade = 1.5
    mo, resp = cb.estimate_market('sell', {'quantity': xbt_to_trade})
    if mo is not None:
        print('sell estimate:{}'.format(mo))
    else:
        print (resp.text)

    xbt_to_trade = 1.5
    mo, resp = cb.estimate_market('buy', {'quantity': xbt_to_trade})
    if mo is not None:
        print('buy estimate: {}'.format(mo))
    else:
        print (resp.text)

    mo, resp = cb.estimate_market('sell', {'amount': 500})
    if mo is not None:
        print('sell estimate:{}'.format(mo))
    else:
        print (resp.text)

    mo, resp = cb.estimate_market('buy', {'amount': 210})
    if mo is not None:
        print('buy estimate: {}'.format(mo))
    else:
        print (resp.text)


    utxns = cb.get_user_transactions()
    print(utxns)