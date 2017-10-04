import time
import requests
import re
import os
import signal
from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Ticker
from expiringdict import ExpiringDict


def show_change(curr_val, prev_val):
    if curr_val < prev_val:
        arrow = ':arrow_down_small:'
    elif curr_val > prev_val:
        arrow = ':arrow_up_small:'
    else:
        arrow = ':arrow_left:'

    return '{val} {arrow}'.format(val=curr_val, arrow=arrow)


def get_my_ip():
    IP='http://ip4.me'
    r = requests.get(IP)
    if r.status_code == 200:
        m=re.search('\d+[.]\d+[.]\d+[.]\d+', r.text)
        if m != None:
            return (m.group())


def usr_handler(signum, frame):
    cb.post_to_slack('user interrupt {}'.format(signum))
    print(signum)
    return


if __name__ == '__main__':
    cache = ExpiringDict(max_len=100, max_age_seconds=3600)
    signal.signal(signal.SIGUSR1, usr_handler)

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

                if 'myip' not in cache:
                    myip = get_my_ip()
                    cb.post_to_slack('ticker connected on {} ({})'.format(os.uname()[1], myip))
                    cache['myip'] = myip
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
