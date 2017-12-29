from flask import Flask
from flask import request
from flask import render_template
from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Ticker
from datetime import timedelta
from datetime import datetime



class PriceChart(Flask):
    session = None

    def set_session(self, session):
        self.session = session


app = PriceChart(__name__)


@app.route('/chart/', methods=['GET'])
def do_chart():
    fromccy = request.args.get('fromccy','XBT')
    period = request.args.get('period','12h')
    if fromccy is None or fromccy not in ['XBT','BCH']:
        fromccy = 'XBT'

    app.logger.info('chart for ccy:{} period:{}'.format(fromccy, period))

    hours=12
    if period.upper() == '12H':
        hours = 12
    elif period.upper() == '1D':
        hours=24
    elif period.upper() == '2D':
        hours=48

    chart_start = datetime.now() - timedelta(hours=hours)


    ticks = app.session.query(Ticker).filter(Ticker.date > chart_start, Ticker.fromccy==fromccy)

    data_txt = 'data.addRows(['
    data = []
    for tick in ticks:
        mid = tick.bid+((tick.ask - tick.bid)/2)

        dt = 'new Date({}, {}, {}, {}, {}, {})'.format(tick.date.year, tick.date.month, tick.date.day, tick.date.hour, tick.date.minute, tick.date.second)
        data.append('[{},{}]'.format(dt, mid))
    data_txt += ','.join(data)
    data_txt += ']);'
    return render_template('chart_head.html', ccy=fromccy)+data_txt+render_template('chart_tail.html')


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)
    app.set_session(session)

    app.run(debug=True, host='0.0.0.0')
