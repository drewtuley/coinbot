import sys
import time

from CoinfloorBot import CoinfloorBot


def calc_cost_price(xbt_amount, txns):
    acc_xbt_bal = 0
    acc_gbp_cost = 0.0
    for txn in txns:
        if txn.raw_type == 2 and txn.gbp < 0:  # buy
            if acc_xbt_bal + (txn.xbt) > xbt_amount:
                partial_amount = xbt_amount - acc_xbt_bal
                acc_gbp_cost += txn.xbt_gbp * partial_amount
                acc_xbt_bal = xbt_amount
            else:
                acc_xbt_bal += txn.xbt
                acc_gbp_cost -= txn.gbp

        if acc_xbt_bal >= xbt_amount:
            break

    return acc_gbp_cost


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
                acc_xbt_bal -= txn.xbt
                acc_gbp_cost += txn.gbp

        if acc_xbt_bal >= xbt_amount:
            break

    return acc_gbp_cost


if __name__ == "__main__":
    cb = CoinfloorBot()
    if len(sys.argv) > 1:
        cb.set_config(sys.argv[1])
    else:
        cb.set_config('coinfloor.props')

    cb.slack_username = 'trader1'
    xbt_to_trade = cb.xbt_to_trade
    min_profit_pc = cb.min_profit_pc
    max_loss_pc = cb.max_loss_pc

    my_balance = cb.get_balance()
    recent_transactions = cb.get_user_transactions()

    if my_balance.xbt_available > 0:
        # looking to sell
        print('Selling')
        cost_price = calc_cost_price(xbt_to_trade, recent_transactions)
        msg = 'Last bought {} XBT for {} GBP ({})'.format(xbt_to_trade, cost_price, cost_price / xbt_to_trade)
        print(msg)
        cb.post_to_slack(msg)
        waiting = True
        prev_mo = None
        sell_actual = True
        while waiting:
            mo, resp = cb.estimate_market('sell', {'quantity': xbt_to_trade})
            if mo is not None and not mo.__eq__(prev_mo):
                prev_mo = mo
                pl = mo.total - cost_price
                pl_pc = pl / cost_price
                msg = 'Market Sell: {} ({}) [p/l: {} {:2.2%}]'.format(mo, mo.price(), pl, pl_pc)
                print(msg)
                cb.post_to_slack(msg)
                if mo.total > cost_price + (cost_price * min_profit_pc):
                    print('in profit')
                    if sell_actual:
                        mor, resp = cb.place_market_order('sell', {'quantity': xbt_to_trade})

                        print('debug: {}'.format(resp.text))
                        if mor is not None:
                            print('MOR: {} resp {}'.format(mor, resp.json()))

                        my_balance = cb.get_balance()
                        cb.post_to_slack('Sold {} XBT - balance info: {}'.format(xbt_to_trade, str(my_balance)))

                        waiting = False
                elif mo.total < cost_price:
                    loss = mo.total - cost_price
                    loss_pc = loss / cost_price
                    print(
                    'potential loss [p/l {loss} ({loss_pc:2.1%}) max={max:2.1%}]'.format(loss=loss, loss_pc=loss_pc,
                                                                                         max=max_loss_pc))
                    if loss_pc < max_loss_pc:
                        msg = 'time to cut losses: [p/l: {pl} ({plpc:2.1%})]'.format(pl=loss, plpc=loss_pc)
                        print(msg)
                        cb.post_to_slack(msg)
                        if sell_actual:
                            mor, resp = cb.place_market_order('sell', {'quantity': xbt_to_trade})

                            print('debug: {}'.format(resp.text))
                            if mor is not None:
                                print('MOR: {} resp {}'.format(mor, resp.json()))

                            my_balance = cb.get_balance()
                            cb.post_to_slack('Sold {} XBT - balance info: {}'.format(xbt_to_trade, str(my_balance)))

                            waiting = False
                else:
                    min_sale_price = cost_price + (cost_price * min_profit_pc)
                    msg = 'wait for price to go up {} ({})'.format(min_sale_price,
                                                                   (min_sale_price) / xbt_to_trade)
                    print(msg)
                    cb.post_to_slack(msg)

            time.sleep(1)

    else:
        print('Buying')
        sale_price = calc_sale_price(xbt_to_trade, recent_transactions)
        msg = 'Last sold {} XBT for {} GBP ({})'.format(xbt_to_trade, sale_price, sale_price / xbt_to_trade)
        print(msg)
        cb.post_to_slack(msg)

        waiting = True
        prev_mo = None
        buy_actual = True
        while waiting:
            mo, resp = cb.estimate_market('buy', {'quantity': xbt_to_trade})
            if mo is not None and not mo.__eq__(prev_mo):
                prev_mo = mo
                pl = sale_price - mo.total
                msg = 'Market Buy: {mo} ({price}) [p/l: {pl} {plpc:2.2%}]'.format(mo=mo, price=mo.price(), pl=pl,
                                                                                  plpc=pl / sale_price)
                print(msg)
                cb.post_to_slack(msg)
                if mo.total < sale_price - (sale_price * min_profit_pc):
                    print('time to buy')
                    if buy_actual:
                        mor, resp = cb.place_market_order('buy', {'quantity': xbt_to_trade})
                        print('debug: {}'.format(resp.text))
                        if mor is not None:
                            print('MOR: {} resp {}'.format(mor, resp.json()))

                        my_balance = cb.get_balance()
                        cb.post_to_slack('Bought {} XBT - balance info: {}'.format(xbt_to_trade, str(my_balance)))

                        waiting = False
                else:
                    min_buy_price = sale_price - (sale_price * min_profit_pc)
                    msg = 'wait for price to drop to {} ({})'.format(min_buy_price, (min_buy_price) / xbt_to_trade)
                    print(msg)
                    cb.post_to_slack(msg)

            time.sleep(1)
    cb.post_to_slack('finished')
