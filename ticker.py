from CoinfloorBot import CoinfloorBot
import time


def show_change(curr_val, prev_val):
    if curr_val < prev_val:
        arrow = ':arrow_down_small:'
    elif curr_val > prev_val:
        arrow = ':arrow_up_small:'
    else:
        arrow = ':arrow_left:'

    return '{val} {arrow}'.format(val = curr_val, arrow = arrow)


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')

    prev_t = cb.get_ticker()
    
    loop_wait = 15
    while loop_wait > 0:
        try:
            t = cb.get_ticker()
            if t is not None and not t.compare(prev_t):
                volchange = t.volume - prev_t.volume
                message = '{dt} bid: {bid} ask: {ask} - last: {last}  vol(24H): {vol} ({vc})'\
                    .format(dt = t.date, bid = show_change(t.bid, prev_t.bid), ask = show_change(t.ask, prev_t.ask),
                        last=show_change(t.last, prev_t.last), vol=t.volume, vc=volchange)
                cb.post_to_slack(message)
                prev_t = t
        except Exception:
            pass

        with open('ticker.loop') as fd:
            for line in fd:
                try:
                    loop_wait = int(line.strip())
                except ValueError:
                    pass

        time.sleep(loop_wait)
