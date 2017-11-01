import os
import time
from slackclient import SlackClient
from CoinfloorBot import CoinfloorBot
import ConfigParser


cb = CoinfloorBot()
cb.set_config('coinfloor.props')
my_parser = ConfigParser.SafeConfigParser()
my_parser.read('coinfloor.props')

# starterbot's ID as an environment variable
bot_id = my_parser.get('bot','bot_id')
slack_bot_token = my_parser.get('bot','slack_bot_token')

# constants
AT_BOT = "<@" + bot_id + ">"
EXAMPLE_COMMAND = "do"
HELP = 'help'

# instantiate Slack & Twilio clients
slack_client = SlackClient(slack_bot_token)

def show_balance():
    balance = cb.get_balance()
    text = '```Balance: {}'.format(balance)

    if balance.xbt_available > 0:
        mo, resp = cb.estimate_market('sell', {'quantity': balance.xbt_available})
        if mo is not None:
            text += '\nGBP cash valuation: {} @ {}'.format(mo, mo.price())
            text += '\nTotal Cash Valuation: {}'.format(mo.total + balance.gbp_balance)
        else:
            text += 'unable to get estimate sell market: status: {} value {}'.format(resp.status_code, resp.value)
    text += '```'

    return text

def handle_command(command, channel, user):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    print('Command:{} Channel: {} User: {}'.format(command, channel, user))
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
    elif command.startswith(HELP):
        response = 'Hi <@{}> I can do the following:\n*buy* - buy coins\n*sell* - sell coins'.format(user)
    elif command == 'show balance':
        response = show_balance()
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
                       output['channel'], output['user']
    return None, None, None


if __name__ == "__main__":

    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("CoinTraderbot connected and running!")
        while True:
            command, channel, user = parse_slack_output(slack_client.rtm_read())
            if command and channel and user:
                handle_command(command, channel, user)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
