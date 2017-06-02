import time

from CoinfloorBot import CoinfloorBot


def calc_cost_price(xbt_amount, txns):
    acc_xbt_bal = 0
    acc_gbp_cost = 0.0
    for txn in txns:
        if txn.raw_type == 2 and txn.gbp < 0:  # buy
            acc_xbt_bal += txn.xbt
            acc_gbp_cost += txn.gbp

        if acc_xbt_bal >= xbt_amount:
            break

    return acc_gbp_cost * -1.0


def calc_sale_price(xbt_amount, txns):
    acc_xbt_bal = 0
    acc_gbp_cost = 0.0
    for txn in txns:
        if txn.raw_type == 2 and txn.gbp > 0:  # sell
            if acc_xbt_bal + (txn.xbt * -1) > xbt_amount:
                partial_amount = xbt_amount - acc_xbt_bal
                acc_gbp_cost += txn.xbt_gbp * partial_amount
                acc_xbt_bal = xbt_amount
            else:
                acc_xbt_bal += txn.xbt * -1
                acc_gbp_cost += txn.gbp

        if acc_xbt_bal >= xbt_amount:
            break

    return acc_gbp_cost


if __name__ == "__main__":
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    xbt_to_trade = 0.2
    gbp_profit = 2.0

    my_balance = cb.get_balance()
    recent_transactions = cb.get_user_transactions()

    if my_balance.xbt_available > 0:
        # looking to sell
        print('Selling')
        cost_price = calc_cost_price(my_balance.xbt_available, recent_transactions)
        print(cost_price)

        waiting = True
        while waiting:
            mo, resp = cb.estimate_market('sell', {'quantity': xbt_to_trade})
            if mo is not None:
                print('Market Sell: {}'.format(mo))
                if mo.total > cost_price + gbp_profit:
                    print('sell sell sell')
                    waiting = False
                else:
                    print('wait for price to go up')

            time.sleep(1)

    else:
        print('Buying')
        sale_price = calc_sale_price(xbt_to_trade, recent_transactions)
        print('Last bought {} XBT for {} GBP'.format(xbt_to_trade, sale_price))

        waiting = True
        while waiting:
            mo, resp = cb.estimate_market('buy', {'quantity': xbt_to_trade})
            if mo is not None:
                print('Market Buy: {}'.format(mo))
                if mo.total < sale_price - gbp_profit:
                    print('buy buy buy')
                    waiting = False
                else:
                    print('wait for price to drop to {}'.format(sale_price - gbp_profit))

            time.sleep(1)
