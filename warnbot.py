import ConfigParser
import copy
import logging
import requests
import time
import re
import os
from datetime import datetime
from expiringdict import ExpiringDict

from parse import *
from persistqueue import PDict
from slackclient import SlackClient

from CoinfloorBot import CoinfloorBot


# constants
HELP = 'help'
HELP_MESSAGE = '```Usage:\n    @warnbot when <coins> [above|below|changes] <value>\n    @warnbot list\n' \
               '    @warnbot clear\n\nExamples:\n' \
               '    @warnbot when 1 XBT above 7000   # warn me when the price of 1 XBT rises above 7000 GBP\n' \
               '    @warnbot when 1.5 BCH below 7890   # warn me when 1.5 BCH prices above 7890 GBP\n' \
               '    @warnbot when 2.3 XBT changes -5    # warn me when the price of 2.3 XBT drops by 5%```'

HWM = 1
LWM = 2
watermark_msgs = {HWM: 'rises above', LWM: 'falls below'}

repeat_count = 3

coin_channels = {}
warnings = {}
coin_bot = {}


class Warning:
    def __init__(self, warntype, channel, user, coins, ccy, value):
        self.warntype = warntype
        self.channel = channel
        self.user = user
        self.coins = coins
        self.ccy = ccy
        self.value = value
        self.repeat_count = repeat_count

    def dec_count(self):
        self.repeat_count -= 1





def get_my_ip():
    ip = 'http://ip4.me'
    r = requests.get(ip)
    if r.status_code == 200:
        m = re.search('\d+[.]\d+[.]\d+[.]\d+', r.text)
        if m != None:
            return (m.group())


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


def get_coin_value(amount, ccy):
    cb = coin_bot[ccy]
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
        ccy = str(p['ccy']).upper()
        value = float(p['value'])
        return coins, ccy, value
    except ValueError:
        return None, None, None


def get_register_msg(coins, ccy, watermark, value):
    return 'registered a warning when the value of {coins} {ccy} {bar} {value} GBP'.format(coins=coins, ccy=ccy,
                                                                                           bar=watermark_msgs[
                                                                                               watermark],
                                                                                           value=value)


def register_watermark(watermark, p, channel, user, ts):
    coins, ccy, value = get_values_a(p)
    logging.debug('coins: {coins} ccy: {ccy} value: {value}'.format(coins=coins, ccy=ccy, value=value))
    if coins is None or ccy not in ['XBT', 'BCH']:
        return None
    w = Warning(watermark, channel, user, coins, ccy, value)
    add_warning(w, ts)
    response = get_register_msg(coins, ccy, watermark, value)

    return response


def register_change(p, channel, user, ts):
    coins, ccy, pcchange = get_values_a(p)
    if coins is None or ccy not in ['XBT', 'BCH']:
        return None
    rtvalue = get_coin_value(coins, ccy)
    if rtvalue is not None:
        value = rtvalue + (rtvalue * (pcchange / 100.0))
        if pcchange > 0:
            w = Warning(HWM, channel, user, coins, ccy, value)
            add_warning(w, ts)
            response = get_register_msg(coins, ccy, HWM, value)
        else:
            w = Warning(LWM, channel, user, coins, ccy, value)
            add_warning(w, ts)
            response = get_register_msg(coins, ccy, LWM, value)
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


watermark = HWM | LWM
change = 4
warning_specs = {'when {coins} {ccy} above {value}': HWM,
                 'when {coins} {ccy} below {value}': LWM,
                 'when {coins} {ccy} changes {value}': change}


def register_warning(command, channel, user, ts):
    logging.debug(command)

    response = HELP_MESSAGE
    for spec in warning_specs:
        p = parse(spec, command)
        if p:
            if warning_specs[spec] & watermark == warning_specs[spec] :
                r = register_watermark(warning_specs[spec], p, channel, user, ts)
            elif warning_specs[spec] == change:
                r = register_change(p, channel, user, ts)
            if r is not None:
                response = r
                break

    return response


def show_warnings(iuser):
    msg = ''
    idx = 1
    for ts in warnings:
        warning = get_warning(ts)
        if iuser == warning.user:
            msg = msg + '{idx}: {msg}\n'.format(idx=idx,
                                                msg=get_register_msg(warning.coins, warning.ccy, warning.warntype,
                                                                     warning.value))
            idx += 1

    if msg != '':
        return '```' + msg + '```'
    else:
        return 'No warnings'


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


def process_housekeep():
    if 'myip' not in cache:
        myip = get_my_ip()
        cache['myip'] = myip
        if myip != warnings_backup['myip']:
            warnings_backup['myip'] = myip
            for channel_name in coin_channels:
                logging.debug('set topic on {}'.format(channel_name))
                ccy = channel_name[10:]
                topic = 'Watching {} on {} - Chart on http://andrewtuley.com/chart?fromccy={}'.format(ccy.upper(), os.uname()[1], ccy.upper())
                slack_client.api_call('channels.setTopic', channel=coin_channels[channel_name], topic=topic)


def process_warnings():
    tozap = []
    coin_value_cache = {'XBT': {}, 'BCH': {}}
    for ts in warnings:
        logging.debug(warnings[ts])
        resp = None
        warning = get_warning(ts)
        try:
            rtvalue = coin_value_cache[warning.ccy][warning.coins]
        except KeyError:
            rtvalue = get_coin_value(warning.coins, warning.ccy)
            if rtvalue is not None:
                coin_value_cache[warning.ccy][warning.coins] = rtvalue

                coin_value_cache[warning.ccy][warning.coins] = rtvalue

        if rtvalue is not None:
            logging.debug('value of {} {} is {:,.2f} @ {:.2f}'.format(warning.coins, warning.ccy, rtvalue,
                                                                      float(rtvalue / warning.coins)))
            if warning.warntype == HWM and rtvalue > warning.value:
                resp = 'Warning <@{}>: value of {} {} has risen above {} to {}'.format(warning.user, warning.coins,
                                                                                       warning.ccy,
                                                                                       warning.value, rtvalue)
                warning.dec_count()
            elif warning.warntype == LWM and rtvalue < warning.value:
                resp = 'Warning <@{}>: value of {} {} has dropped below {} to {}'.format(warning.user, warning.coins,
                                                                                         warning.ccy,
                                                                                         warning.value, rtvalue)
                warning.dec_count()

            if warning.repeat_count <= 0:
                tozap.append(ts)
            if resp is not None:
                logging.debug('post to slack {}'.format(resp))
                slack_client.api_call("chat.postMessage", channel=warning.channel,
                                      text=resp, as_user=True)
        else:
            logging.warning('Unable to get realtime value of {} {}'.format(warning.coins, warning.ccy))

    for ts in tozap:
        remove_warning(ts)


def handle_command(command, channel, user, ts):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *help* command "
    command = re.sub('[ ]{2,}', ' ', command)
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
    elif command.startswith('set the channel topic'):
        response = None
    

    if response is not None:
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

    cb_xbt = CoinfloorBot()
    cb_xbt.set_config('coinfloor.props')
    cb_bch = CoinfloorBot(fromccy='BCH')
    cb_bch.set_config('coinfloor.props')

    coin_bot['XBT'] = cb_xbt
    coin_bot['BCH'] = cb_bch

    config = ConfigParser.SafeConfigParser()
    config.read('warnbot.props')

    dt = str(datetime.now())[:10]
    logging.basicConfig(format='%(asctime)s %(message)s',
                        filename=config.get('warnbot', 'logfile') + dt + '.log',
                        level=logging.DEBUG)
    logging.captureWarnings(True)

    cache = ExpiringDict(max_len=10, max_age_seconds=3600)
    warnings_backup = PDict('data', 'warnbot')
    for k in warnings_backup['keys']:
        warnings[k] = warnings_backup[k]

    if len(warnings) > 0:
        logging.info('Loaded {} warnings from storage'.format(len(warnings)))

    try:
        repeat_count = warnings_backup['repeat']
    except KeyError:
        pass

    warnings_backup['repeat'] = repeat_count

    try:
        myip = warnings_backup['myip']
        cache['myip'] = myip
    except KeyError:
        pass

    # warnbot's ID in config file
    bot_id = config.get('warnbot', 'bot_id')
    AT_BOT = "<@" + bot_id + ">"
    slack_bot_token = config.get('warnbot', 'slack_bot_token')

    # instantiate Slack & Twilio clients
    slack_client = SlackClient(slack_bot_token)


    READ_WEBSOCKET_DELAY = 1  # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        logging.debug("warnbot connected and running!")
        channels = slack_client.api_call('channels.list',exclude_archive='True', exclude_members='True')
        logging.debug(len(channels['channels']))
        for channel in channels['channels']:
            if channel['name'].startswith('coinfloor-'):
                logging.debug('{} {}'.format(channel['name'], channel['id']))
                coin_channels[channel['name']] = channel['id']

        while True:
            command, channel, user, ts = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user, ts)
            process_warnings()
            process_housekeep()
            time.sleep(READ_WEBSOCKET_DELAY)
