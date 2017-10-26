# Most of this bot was built from this source https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
# Notable shout out to https://www.dataquest.io/blog/ for their many python tutorials

import os
import time
from slackclient import SlackClient
import requests
import json


# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# convert the bot ID into a useful string
AT_BOT = "<@" + BOT_ID + ">"

# programmed commands for the slackbot
EXAMPLE_COMMAND = "do"
GET_BTC = "btc"
GET_ETH = "eth"
GET_LTC = "ltc"
GET_OMG = "omg"
HELP = "help"
UPDATE_ETH = "update eth"
UPDATE = "update"

# defining currencies for Bittrex
# The API for Bitttrex can be found here: https://bittrex.com/home/api
# The list of supported markets can be found here: https://bittrex.com/api/v1.1/public/getmarkets
# For this script we are pulling four currencies (Bitcoin, LightCoin, OmiseGO, and Etherum) with values relative to the US Dollar
btc="USDT-BTC"
ltc="USDT-LTC"
omg="USDT-OMG"
eth="USDT-ETH"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Whatever you typed in is not programed right now. If you want that, talk to Kip."
    
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
        
    if command.startswith(HELP):
        response = "Use the following: \n@cryptobot btc \n@cryptobot eth \n@cryptobot ltc \n@cryptobot omg \n@cryptobot update"

    # this is a simple set of commands to pull the data from bittrex and grab the last trade
    # the api calls gets an odd nested dictionary-list-dictionary
    if command.startswith(GET_BTC):
        url="https://bittrex.com/api/v1.1/public/getticker?market=USDT-BTC"
        response = requests.get(url)
        data = response.json()
        trades = data["result"]
        lasttrade=trades["Last"]
        response = "Current price for Bitcoin is $" + str(lasttrade)


    if command.startswith(GET_ETH):
        url="https://bittrex.com/api/v1.1/public/getticker?market=USDT-ETH"
        response = requests.get(url)
        data = response.json()
        trades = data["result"]
        lasttrade=trades["Last"]
        response = "Current price for Etherum is $" + str(lasttrade)

    if command.startswith(GET_LTC):
        url="https://bittrex.com/api/v1.1/public/getticker?market=USDT-LTC"
        response = requests.get(url)
        data = response.json()
        trades = data["result"]
        lasttrade=trades["Last"]
        response = "Current price for LightCoin is $" + str(lasttrade)

    if command.startswith(GET_OMG):
        url="https://bittrex.com/api/v1.1/public/getticker?market=USDT-OMG"
        response = requests.get(url)
        data = response.json()
        trades = data["result"]
        lasttrade=trades["Last"]
        response = "Current price for OmiseGo is $" + str(lasttrade)

    # Update gets the latest trade for all currencies
    if command.startswith(UPDATE):
        #create two arrays: one for text output and the other with the Bittrex market name 
        currencies=[btc, ltc, omg, eth]
        names=["BTC", "LTC", "OMG", "ETH"]
        endresult="Here is your market update:"
        #a small mutation on the routine above. This runs the routine four times while switching the currency. 
        for x in range(0,4):
           currency=currencies[x]
           url="https://bittrex.com/api/v1.1/public/getticker?market="+currency
           response = requests.get(url)
           data = response.json()
           trades = data["result"]
           lasttrade=trades["Last"]
           result="" + names[x] + " is trading at $" + str(lasttrade)
           #The result text is appended to a string that is pre-formatted for Slack.
           endresult=endresult + " \n " + result
        response = endresult

#DO NOT DELETE. KEEP THIS INSTRUCTION TO SEND REPLY. 
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)


def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None

# part 3 is now in the right spot
if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command.lower(), channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
