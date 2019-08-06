import ConfigParser

from parse import *
from datetime import datetime
import logging
import time
import re
from slackclient import SlackClient

from CoinfloorBot import CoinfloorBot

cb = CoinfloorBot(fromccy='XBT')
cb.set_config('coinfloor.props')
cb_bch = CoinfloorBot(fromccy='BCH')
cb_bch.set_config('coinfloor.props')

config = ConfigParser.SafeConfigParser()
config.read('cointraderbot.props')

dt = str(datetime.now())[:10]
logging.basicConfig(format='%(asctime)s %(message)s',
                    filename=config.get('cointraderbot', 'logfile') + dt + '.log',
                    level=logging.DEBUG)
logging.captureWarnings(True)

# starterbot's ID as an environment variable
bot_id = config.get('cointraderbot', 'bot_id')
slack_bot_token = config.get('cointraderbot', 'slack_bot_token')

# constants
AT_BOT = "<@" + bot_id + ">"
EXAMPLE_COMMAND = "do"
HELP = 'help'

# hash of 'value' requests by user
value_cache = {}
boo_cache = {}
warnings = {}

# instantiate Slack & Twilio clients
slack_client = SlackClient(slack_bot_token)


def show_balance():
    gbp_balance, xbt_balance = cb.get_balance()
    #gbp_balance, bch_balance = cb_bch.get_balance()
    bch_balance = None
    text = '```{}\n{}\n{}'.format(gbp_balance, xbt_balance, bch_balance)
    if xbt_balance.available > 0:
        mo, resp = cb.estimate_market('sell', {'quantity': xbt_balance.available})
        if mo is not None:
            xbt_value = mo.total
            text += '\nXBT cash valuation: {} @ {}'.format(mo, mo.price())
        else:
            text += 'unable to get estimate sell market: status: {} '.format(resp.status_code)
    if bch_balance is not None and bch_balance.available > 0:
        mo, resp = cb_bch.estimate_market('sell', {'quantity': bch_balance.available})
        if mo is not None:
            bch_value = mo.total
            text += '\nBCH cash valuation: {} @ {}'.format(mo, mo.price())
        else:
            text += 'unable to get estimate sell market: status: {} '.format(resp.status_code)
    else:
        bch_value = 0.0
    text += '\nTotal Cash Valuation:       {:,.2f}'.format(xbt_value + bch_value + gbp_balance.balance)
    text += '```'

    return text


def get_value(command, user):
    p = parse('value {amt}', command)
    amount = 0
    # print(p)
    if p and p['amt'] != '':
        amount = p['amt']
    elif user in value_cache:
        amount = value_cache[user]
    text = '```'
    text += get_estimated_value('sell', amount) + '\n'
    text += get_estimated_value('buy', amount)

    text += '```'
    return text


def get_estimated_value(buy_sell, amount):
    text = 'Estimated {} value of {} XBT:'.format(buy_sell, amount)
    mo, resp = cb.estimate_market(buy_sell, {'quantity': amount})
    if mo is not None:
        text += '\nGBP cash valuation: {} @ {}'.format(mo, mo.price())
        value_cache[user] = amount
    else:
        text += 'unable to get estimated {} market: status: {} '.format(buy_sell, resp.status_code)
    logging.info(text)

    return text


def get_estimate(command, user):
    p = parse('estimate {op} {amt}', command)
    if p:
        op = p['op']
        amt = p['amt']
        if op not in ['buy', 'sell']:
            return 'Invalid OPeration "{}" [buy|sell]'.format(op)
        try:
            if float(amt) < 0:
                return 'Invalid amount "{}" - must be >0'.format(amt)
        except ValueError:
            return 'Invalid amount "{}" - must be numeric and >0'.format(amt)

        text = '```Estimated {op} value of {amt} XBT:'.format(amt=amt, op=op)
        mo, resp = cb.estimate_market(op, {'quantity': amt})
        if mo is not None:
            text += '\nGBP cash valuation: {} @ {}'.format(mo, mo.price())
        else:
            text += 'unable to get estimate sell market: status: {} '.format(resp.status_code)

        text += '```'
        return text
    else:
        return 'Invalid operation: {}'.format(command)


def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """

    command = re.sub('[ ]{2,}', ' ', command)
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    logging.debug('Command:{} Channel: {} User: {}'.format(command, channel, user))
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    elif command.startswith(HELP):
        response = 'Hi <@{}> I can do the following:\n*buy* - buy coins\n*sell* - sell coins'.format(user)
    elif command in ['show balance', 'sb']:
        response = show_balance()
    elif command.startswith('value'):
        response = get_value(command, user)
    elif command.startswith('estimate'):
        response = get_estimate(command, user)

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    for o in slack_rtm_output:
        for key in o:
            logging.debug('{}:{}'.format(key, o[key]))
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel'], output['user']
    return None, None, None


if __name__ == "__main__":

    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        logging.debug("CoinTraderbot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)

            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        logging.debug("Connection failed. Invalid Slack token or bot ID?")
