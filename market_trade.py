import sys
import time

from CoinfloorBot import CoinfloorBot

actioned = {'sell': 'Sold', 'buy': 'Bought'}


if __name__ == "__main__":
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    if len(sys.argv) < 3:
        print('Usage: {} [buy|sell] <amount>'.format(sys.argv[0]))
        sys.exit(1)

    trade_op = str(sys.argv[1])
    trade_amount = float(sys.argv[2])

    if trade_op not in ['buy','sell']:
        print('Error; invalid type type {}'.format(trade_op))
        sys.exit(1)

    if trade_amount < 0.0:
        print('Error: cannot trade < 0 XBT')
        sys.exit(1)

    cb.slack_username = 'trader1'

    my_balance = cb.get_balance()
    recent_transactions = cb.get_user_transactions()

    if trade_op == 'sell' and trade_amount > my_balance.xbt_available:
        print('Trade quantity ({}) > XBT available ({})'.format(trade_amount, my_balance.xbt_available))
        sys.exit(1)

    mor, resp = cb.place_market_order(trade_op, {'quantity': trade_amount})

    print('debug: {}'.format(resp.text))
    if mor is not None:
        print('MOR: {} resp {}'.format(mor, resp.json()))

    my_balance = cb.get_balance()
    cb.post_to_slack('{} {} XBT - balance info: {}'.format(actioned[trade_op], trade_amount, str(my_balance)))
