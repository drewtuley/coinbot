import time
from slackclient import SlackClient
from CoinfloorBot import CoinfloorBot
import ConfigParser
from parse import *

cb = CoinfloorBot()
cb.set_config('coinfloor.props')
my_parser = ConfigParser.SafeConfigParser()
my_parser.read('coinfloor.props')

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

# hash of 'value' requests by user
warnings = {}
warning_count = 3

# instantiate Slack & Twilio clients
slack_client = SlackClient(slack_bot_token)


def get_coin_value(amount):
    mo, resp = cb.estimate_market('sell', {'quantity': amount})
    if mo is not None:
        return mo.total
    else:
        return None


def get_values_a(p):
    try:
        coins = float(p['coins'])
        value = float(p['value'])
        return coins, value
    except:
        return None, None


def get_register_msg(coins, watermark, value):
    return 'registered a warning when the value of {coins} XBT {bar} {value} GBP'.format(coins=coins,
                                                                                         bar=watermark_msgs[watermark],
                                                                                         value=value)


def register_watermark(watermark, p, channel, user, ts):
    coins, value = get_values_a(p)
    if coins is None:
        return None
    warnings[ts] = (watermark, channel, user, coins, value, warning_count)
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
            warnings[ts] = (HWM, channel, user, coins, value, warning_count)
            response = get_register_msg(coins, HWM, value)
        else:
            warnings[ts] = (LWM, channel, user, coins, value, warning_count)
            response = get_register_msg(coins, HWM, value)
        return response

    return None


def clear_warnings(user):
    tozap = []
    for ts in warnings:
        if warnings[ts][2] == user:
            tozap.append(ts)
    for ts in tozap:
        warnings.pop(ts)

    return 'all warnings for <@{}> cleared'.format(user)


def register_warning(command, channel, user, ts):
    print(command)

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
        warntype, channel, user, coins, value, count = warnings[ts]
        if iuser == user:
            msg = msg + '{idx}: {msg}\n'.format(idx, get_register_msg(coins, warntype, value))
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
            warnings = int(p['times'])
            response = 'warning repeat set to {}'.format(warnings)
        except:
            pass

    return response


def process_warnings():
    tozap = []
    for ts in warnings:
        print(warnings[ts])
        resp = None
        warntype, channel, user, coins, value, count = warnings[ts]
        rtvalue = get_coin_value(coins)
        print('value of {} is {}'.format(coins, rtvalue))
        if warntype == HWM and rtvalue > value:
            resp = 'Warning <@{}>: value of {} XBT has risen above {} to {}'.format(user, coins, value, rtvalue)
            count -= 1
        elif warntype == LWM and rtvalue < value:
            resp = 'Warning <@{}>: value of {} XBT has dropped below {} to {}'.format(user, coins, value, rtvalue)
            count -= 1
        if count > 0:
            warnings[ts] = (warntype, channel, user, coins, value, count)
        else:
            tozap.append(ts)

        if resp is not None:
            slack_client.api_call("chat.postMessage", channel=channel,
                                  text=resp, as_user=True)

    for ts in tozap:
        warnings.pop(ts)


def handle_command(command, channel, user, ts):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *help* command "
    print('Command:{} Channel: {} User: {}'.format(command, channel, user))
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
            print('{}:{}'.format(key, o[key]))
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
        print("warnbot connected and running!")
        while True:
            command, channel, user, ts = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user, ts)
            process_warnings()
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
