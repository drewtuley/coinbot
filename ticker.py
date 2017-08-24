import time

from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Ticker


def show_change(curr_val, prev_val):
    if curr_val < prev_val:
        arrow = ':arrow_down_small:'
    elif curr_val > prev_val:
        arrow = ':arrow_up_small:'
    else:
        arrow = ':arrow_left:'

    return '{val} {arrow}'.format(val=curr_val, arrow=arrow)


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    session = cb.get_db_session(echo=False)

    prev_t = cb.get_ticker()

    loop_wait = 15
    while loop_wait > 0:
        try:
            t = cb.get_ticker()
            bal = cb.get_balance()
            if t is not None and not t.compare(prev_t):
                volchange = t.volume - prev_t.volume
                if bal is not None:
                    val = t.bid * bal.xbt_balance
                    valdiff = val - (prev_t.bid * bal.xbt_balance)
                else:
                    val = 0
                    valdiff = 0
                message = '{dt} bid: {bid} ask: {ask} - last: {last}  vol(24H): {vol:3.2f} ({vc:2.2f}) val:({val} {valdiff:+3.2f})' \
                    .format(dt=t.date, bid=show_change(t.bid, prev_t.bid), ask=show_change(t.ask, prev_t.ask),
                            last=show_change(t.last, prev_t.last), vol=t.volume, vc=volchange, val=val, valdiff=valdiff)
                cb.post_to_slack(message)
                session.add(t)
                session.commit()
                prev_t = t
        except Exception as err:
            print(err)
            pass

        with open('ticker.loop') as fd:
            for line in fd:
                try:
                    loop_wait = int(line.strip())
                except ValueError:
                    pass

        time.sleep(loop_wait)
