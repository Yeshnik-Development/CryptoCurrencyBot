import os
import time
from slackclient import SlackClient
import GDAX

# part 2

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"
GET_BTC = "btc"
GET_ETH = "eth"
GET_LTC = "ltc"
HELP = "help"
UPDATE_ETH = "update eth"
UPDATE = "update"


# instantiate Slack & Twilio clients and GDAX
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
publicClient = GDAX.PublicClient()


# part 4


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
        response = "Use the following: \n@cryptobot btc \n@cryptobot eth \n@cryptobot ltc \n@cryptobot update eth"

    if command.startswith(GET_BTC):
        # Set a default product
        publicClient = GDAX.PublicClient(product_id="BTC-USD")
        #pull history from last 24 hours - to get last bid
        dataoutput=publicClient.getProduct24HrStats()
        #grab the value of the last trade
        BTCPrice=dataoutput["last"]        
        response = "Current price for Bitcoin is $" + BTCPrice[:7]

    if command.startswith(GET_ETH):
        # Set a default product
        publicClient = GDAX.PublicClient(product_id="ETH-USD")
        #pull history from last 24 hours - to get last bid
        dataoutput=publicClient.getProduct24HrStats()
        #grab the value of the last trade
        ETHPrice=dataoutput["last"]      
        response = "Current price for Ethereum is $" + ETHPrice[:6]

    if command.startswith(GET_LTC):
        # Set a default product
        publicClient = GDAX.PublicClient(product_id="LTC-USD")
        #pull history from last 24 hours - to get last bid
        dataoutput=publicClient.getProduct24HrStats()
        #grab the value of the last trade
        LTCPrice=dataoutput["last"]   
        response = "Current price for Litecoin is $" + LTCPrice[:5]

    if (command.startswith(UPDATE)) or (command.startswith(UPDATE_ETH)):
        publicClient = GDAX.PublicClient(product_id="ETH-USD")
        #pull history from last 24 hours - to get last bid
        dataoutput=publicClient.getProduct24HrStats()
        #grab the value of the last trade
        lastvalueread=dataoutput["last"]
        lastvalue=float(lastvalueread)
        #Get the 24 hour high for another
        highofday=dataoutput["high"]
        highvalue=float(highofday)
        #Get the 24 hour high for another
        lowofday=dataoutput["low"]
        lowvalue=float(lowofday)
        #find the mean between the high and the low
        mean=((highvalue + lowvalue) / 2)
        #calculate the standard devation of the three values 
        #(hahahaha, NOPE. Not a real statistical test but the math will work for this application)
        val1 = (lowvalue-mean)**2
        val2 = (highvalue-mean)**2
        val3 = (lastvalue-mean)**2
        variance = (val1 + val2 + val3)/3
        standev = variance ** 0.5
        #format the value into a string and truncate
        stdev_str=str(standev)
        stdev_print=stdev_str[:4]
        #we are going to call a trend if the last value is more than 1/2 a deviation off the mean
        halfstandev=standev/2
        trend_val=(lastvalue-mean)
        if (trend_val > halfstandev):
            trend_str='positive'	
        elif (trend_val < -halfstandev):
            trend_str='negative'	
        else:
            trend_str='flat'
        response="ETH movement of: "+stdev_print+" % in the last 24hrs! \n \nThe current trend is: "+trend_str+"\n \n24hr High: $"+str(highvalue)+"\n24hr Low: $"+str(lowvalue)+"\nLast: $"+str(lastvalue)

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
