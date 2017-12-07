import copy
import time
from datetime import datetime
from slackclient import SlackClient
from CoinfloorBot import CoinfloorBot
import ConfigParser
from parse import *
from persistqueue import PDict
import logging

cb = CoinfloorBot()
cb.set_config('coinfloor.props')
my_parser = ConfigParser.SafeConfigParser()
my_parser.read('coinfloor.props')

dt = str(datetime.now())[:10]
logging.basicConfig(format='%(asctime)s %(message)s',
                    filename='logs/warnbot_' + dt + '.log',
                    level=logging.DEBUG)
logging.captureWarnings(True)

# warnbot's ID in config file
bot_id = my_parser.get('warnbot', 'bot_id')
slack_bot_token = my_parser.get('warnbot', 'slack_bot_token')

# constants
AT_BOT = "<@" + bot_id + ">"
HELP = 'help'
HELP_MESSAGE = '```Usage:\n    @warnbot when <coins> [above|below|changes] <value>\n    @warnbot list\n' \
               '    @warnbot clear\n\nExamples:\n' \
               '    @warnbot when 1 above 7000   # warn me when the price of 1 XBT rises above 7000 GBP\n' \
               '    @warnbot when 1.5 below 7890   # warn me when 1.5 XBT prices above 7890 GBP\n' \
               '    @warnbot when 2.3 changes -5    # warn me when the price of 2.3XBT drops by 5%```'

HWM = 1
LWM = 2
watermark_msgs = {HWM: 'rises above', LWM: 'falls below'}

repeat_count = 3


class Warning:
    def __init__(self, warntype, channel, user, coins, value):
        self.warntype = warntype
        self.channel = channel
        self.user = user
        self.coins = coins
        self.value = value
        self.repeat_count = repeat_count

    def dec_count(self):
        self.repeat_count -= 1


warnings = {}
warnings_backup = PDict('data', 'warnbot')
for k in warnings_backup['keys']:
    warnings[k] = warnings_backup[k]

try:
    repeat_count = warnings_backup['repeat']
except KeyError:
    pass

warnings_backup['repeat'] = repeat_count

# instantiate Slack & Twilio clients
slack_client = SlackClient(slack_bot_token)


def regen_keys():
    keys = copy.copy(warnings.keys())
    warnings_backup['keys'] = keys


def add_warning(warning, index):
    warnings[index] = warning
    warnings_backup[index] = warning
    regen_keys()


def remove_warning(index):
    del warnings[index]
    del warnings_backup[index]
    regen_keys()


def get_warning(index):
    return warnings[index]


def get_coin_value(amount):
    try:
        mo, resp = cb.estimate_market('sell', {'quantity': amount})
        if mo is not None:
            return mo.total
        else:
            return None
    except:
        logging.error('failed to get coin value')
        return None


def get_values_a(p):
    try:
        coins = float(p['coins'])
        value = float(p['value'])
        return coins, value
    except ValueError:
        return None, None


def get_register_msg(coins, watermark, value):
    return 'registered a warning when the value of {coins} XBT {bar} {value} GBP'.format(coins=coins,
                                                                                         bar=watermark_msgs[watermark],
                                                                                         value=value)


def register_watermark(watermark, p, channel, user, ts):
    coins, value = get_values_a(p)
    if coins is None:
        return None
    w = Warning(watermark, channel, user, coins, value)
    add_warning(w, ts)
    response = get_register_msg(coins, watermark, value)

    return response


def register_change(p, channel, user, ts):
    coins, pcchange = get_values_a(p)
    if coins is None:
        return None
    rtvalue = get_coin_value(coins)
    if rtvalue is not None:
        value = rtvalue + (rtvalue * (pcchange / 100.0))
        if pcchange > 0:
            w = Warning(HWM, channel, user, coins, value)
            add_warning(w, ts)
            response = get_register_msg(coins, HWM, value)
        else:
            w = Warning(LWM, channel, user, coins, value)
            add_warning(w, ts)
            response = get_register_msg(coins, LWM, value)
        return response

    return None


def clear_warnings(user):
    tozap = []
    for ts in warnings:
        warning = get_warning(ts)
        if warning.user == user:
            tozap.append(ts)

    for ts in tozap:
        remove_warning(ts)

    return 'all warnings for <@{}> cleared'.format(user)


def register_warning(command, channel, user, ts):
    logging.debug(command)

    response = HELP_MESSAGE
    p = parse('when {coins} below {value}', command)
    if p:
        r = register_watermark(LWM, p, channel, user, ts)
        if r is not None:
            response = r
    p = parse('when {coins} above {value}', command)
    if p:
        r = register_watermark(HWM, p, channel, user, ts)
        if r is not None:
            response = r
    p = parse('when {coins} changes {value}', command)
    if p:
        r = register_change(p, channel, user, ts)
        if r is not None:
            response = r

    return response


def show_warnings(iuser):
    msg = ''
    idx = 1
    for ts in warnings:
        warning = get_warning(ts)
        if iuser == warning.user:
            msg = msg + '{idx}: {msg}\n'.format(idx=idx,
                                                msg=get_register_msg(warning.coins, warning.warntype, warning.value))
            idx += 1

    if msg != '':
        return '```' + msg + '```'
    else:
        return ''


def set_repeat(command):
    response = 'invalid repeat command: {}'.format(command)
    p = parse('repeat {times}', command)
    if p:
        try:
            repeat_count = int(p['times'])
            response = 'warning repeat set to {}'.format(repeat_count)
            warnings_backup['repeat'] = repeat_count
        except ValueError:
            pass

    return response


def process_warnings():
    tozap = []
    coin_value_cache = {}
    for ts in warnings:
        logging.debug(warnings[ts])
        resp = None
        warning = get_warning(ts)
        try:
            rtvalue = coin_value_cache[warning.coins]
        except KeyError:
            rtvalue = get_coin_value(warning.coins)
            coin_value_cache[warning.coins] = rtvalue

        logging.debug('value of {} is {}'.format(warning.coins, rtvalue))
        if warning.warntype == HWM and rtvalue > warning.value:
            resp = 'Warning <@{}>: value of {} XBT has risen above {} to {}'.format(warning.user, warning.coins,
                                                                                    warning.value, rtvalue)
            warning.dec_count()
        elif warning.warntype == LWM and rtvalue < warning.value:
            resp = 'Warning <@{}>: value of {} XBT has dropped below {} to {}'.format(warning.user, warning.coins,
                                                                                      warning.value, rtvalue)
            warning.dec_count()

        if warning.repeat_count <= 0:
            tozap.append(ts)
        if resp is not None:
            logging.debug('post to slack {}'.format(resp))
            slack_client.api_call("chat.postMessage", channel=warning.channel,
                                  text=resp, as_user=True)

    for ts in tozap:
        remove_warning(ts)


def handle_command(command, channel, user, ts):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *help* command "
    logging.debug('Command:{} Channel: {} User: {}'.format(command, channel, user))
    if command.startswith(HELP):
        response = HELP_MESSAGE
    elif command.startswith('when'):
        response = register_warning(command, channel, user, ts)
    elif command.startswith('clear'):
        response = clear_warnings(user)
    elif command.startswith('list'):
        response = show_warnings(user)
    elif command.startswith('repeat'):
        response = set_repeat(command)

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
                       output['channel'], output['user'], output['ts']
    return None, None, None, None


if __name__ == "__main__":

    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        logging.debug("warnbot connected and running!")
        while True:
            command, channel, user, ts = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user, ts)
            process_warnings()
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        logging.error("Connection failed. Invalid Slack token or bot ID?")
