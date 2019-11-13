import logging
import logging.handlers
import os
import re
import sys
import time
from datetime import datetime

import requests
from expiringdict import ExpiringDict

from CoinfloorBot import CoinfloorBot


def show_change(curr_val, prev_val):
    if curr_val < prev_val:
        arrow = ':arrow_down_small_red:'
    elif curr_val > prev_val:
        arrow = ':arrow_up_small_green:'
    else:
        arrow = ':arrow_left:'

    return '{val} {arrow}'.format(val=curr_val, arrow=arrow)


def get_my_ip():
    ip = 'http://ip4.me'
    r = requests.get(ip)
    if r.status_code == 200:
        m = re.search('\d+[.]\d+[.]\d+[.]\d+', r.text)
        if m != None:
            return (m.group())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        fromccy = sys.argv[1]
    else:
        fromccy = 'XBT'

    cache = ExpiringDict(max_len=100, max_age_seconds=3600)

    cb = CoinfloorBot(fromccy=fromccy)
    cb.set_config('coinfloor.props')

    session = cb.get_db_session(echo=False)
    prev_t = cb.get_ticker()

    dt = str(datetime.now())[:10]
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.handlers.TimedRotatingFileHandler('logs/ticker_'+fromccy.lower()+'.log', when='midnight', interval=1, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    loop_wait = 15
    while loop_wait > 0:
        try:
            t = cb.get_ticker()
            logging.info(t)
            gbp_bal, from_bal = cb.get_balance()
            logger.info(gbp_bal)
            if t is not None and not t.compare_significant(prev_t):
                volchange = t.volume - prev_t.volume
                if from_bal is not None:
                    val = t.bid * from_bal.balance
                    valdiff = val - (prev_t.bid * from_bal.balance)
                else:
                    val = 0
                    valdiff = 0

                message = '{dt} high: {hi} low: {lo} bid: {bid} ask: {ask} - last: {last}  vol(24H): {vol:3.2f} ({vc:2.2f})' \
                    .format(dt=str(t.date)[10:], bid=show_change(t.bid, prev_t.bid), ask=show_change(t.ask, prev_t.ask),
                            last=show_change(t.last, prev_t.last), vol=t.volume, vc=volchange, lo=t.low, hi=t.high)
                logger.info(message)
                cb.post_to_slack(message)
                logger.info('posted')
                session.add(t)
                session.commit()
                prev_t = t

                if 'myip' not in cache:
                    myip = get_my_ip()
                    cb.post_to_slack('ticker connected on {} ({})'.format(os.uname()[1], myip))
                    cache['myip'] = myip
        except Exception as err:
            logger.error(err)
            pass

        with open('ticker.loop') as fd:
            for line in fd:
                try:
                    loop_wait = int(line.strip())
                except ValueError:
                    pass

        time.sleep(loop_wait)
