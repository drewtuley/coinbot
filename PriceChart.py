from flask import Flask
from flask import request
from CoinfloorBot import CoinfloorBot
from CoinfloorBot import Ticker
from datetime import timedelta
from datetime import datetime



class PriceChart(Flask):
    session = None

    def set_session(self, session):
        self.session = session


app = PriceChart(__name__)


line_chart_header = '''
  <html>
  <head>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
    google.charts.load('current', {packages: ['corechart', 'line']});
    google.charts.setOnLoadCallback(drawTrendlines);

    function drawTrendlines() {
      var data = new google.visualization.DataTable();
      data.addColumn('datetime', 'X');
'''
yaxis='''data.addColumn('number', 'Mid Price: {ccy}');
'''
line_chart_footer = '''
      var options = {
        hAxis: {
          title: 'Time'
        },
        vAxis: {
          title: 'Price'
        },
        colors: ['#AB0D06', '#007329'],
        trendlines: {
          0: {type: 'linear', color: '#111', opacity: .3},
          1: {type: 'exponential', color: '#222', opacity: .3}
        }
      };

      var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
      chart.draw(data, options);
    }
    </script>
  </head>
  <body>
    <div id="chart_div" style="width: 900px; height: 500px"></div>
  </body>
</html>
'''

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
    return line_chart_header+yaxis.format(ccy=fromccy)+data_txt+line_chart_footer


if __name__ == '__main__':
    cb = CoinfloorBot()
    cb.set_config('coinfloor.props')
    session = cb.get_db_session(echo=False)
    app.set_session(session)

    app.run(debug=True, host='0.0.0.0')
