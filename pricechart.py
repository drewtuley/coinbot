from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory
from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Ticker
from datetime import timedelta
from datetime import datetime
from dotmap import DotMap
import os



class PriceChart(Flask):
    session = None

    def set_session(self, session):
        self.session = session


app = PriceChart(__name__)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/chart/', methods=['GET'])
def do_chart():
    meta = DotMap()
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

    meta.fetch.start = datetime.now()
    ticks = app.session.query(Ticker).filter(Ticker.date > chart_start, Ticker.fromccy==fromccy)
    smoothed = []
    smooth_index = {}
    sm_idx = -1
    for tick in ticks:
        dt = tick.date.replace(second=0, microsecond=0)
        if dt in smooth_index:
            sm_idx = smooth_index[dt]
            mids=smoothed[sm_idx]
            mids.append(tick.bid+((tick.ask - tick.bid)/2))
            smoothed[sm_idx] = mids
        else:
            mids = []
            sm_idx += 1
            smooth_index[dt] = sm_idx
            mids.append(tick.bid+((tick.ask - tick.bid)/2))
            smoothed.append(mids)
    
    meta.fetch.end = datetime.now()
    rev_index = {}
    for smidx in smooth_index:
        rev_index[smooth_index[smidx]] = smidx

    meta.dataform.start = datetime.now()
    data_txt = 'data.addRows(['
    data = []
    for sm_idx in rev_index:
        smooth_date = rev_index[sm_idx]
        count = 0
        midsum = 0
        for mid in smoothed[sm_idx]:
            midsum += mid
            count += 1
        mid = midsum / count
        
        dt = 'new Date({}, {}, {}, {}, {}, {})'.format(smooth_date.year, smooth_date.month-1, smooth_date.day, smooth_date.hour, smooth_date.minute, smooth_date.second)
        data.append('[{},{}]'.format(dt, mid))

    data_txt += ','.join(data)
    data_txt += ']);'
    meta.dataform.end = datetime.now()

    return render_template('pricechart.html', ccy=fromccy, data=data_txt, meta=meta)


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)
    app.set_session(session)

    app.run(debug=False, host='0.0.0.0')
