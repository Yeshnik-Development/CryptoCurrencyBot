import os
import time
from slackclient import SlackClient
import requests
import json
from math import floor, log10

# Make it work for Python 2+3 and with Unicode
import io
try:
    to_unicode = unicode
except NameError:
    to_unicode = str

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
GET_STATS = "stats"

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


def get_currency_stats():
   message=""
      
   #define currency varibles for bittrex
   btc="USDT-BTC"
   eth="USDT-ETH"
   omg="USDT-OMG"
   currencies=[btc, eth, omg]
   names=["BTC", "ETH", "OMG" ]
   statvals_dict={}
   # Thresholds gives us an event trigger
   # The normal swings of the currencies are $300 for BTC, $20 for ETH, and $0.50 for OMG 
   # Below we use a linear approximation of what these triggers should be
   # If you compare these values to the current prices for the currencies you get the following swings:
   # 4.5% for BTC, 6% for ETH, and 8.4% for OMG
   #thresholds=[4.5, 6, 8.4]

   #Run this loop 3 times, once for each currency
   for x in range(0,3):

      #get the currency and get the data from bittrex
      currency=currencies[x]
      url="https://bittrex.com/api/v1.1/public/getmarketsummary?market="+currency
      response = requests.get(url)
      data = response.json()
      trades= data["result"][0]
      lastvalue=trades["Last"]
      lowvalue=trades["Low"]
      highvalue=trades["High"]

      # We're going to grab the data from the current trade database
      # This database is created by Bittrex_DB_Populate.py
      with open('/home/pi/Development/CryptoDB.json') as data_file:    
         DBdata = json.load(data_file)

      #grab the 3 letter name which is the dictionary entry for the currency data
      directory=names[x]

      #reset three varibles
      summation=0
      variancesum=0
      sigxy_sum=0

      #pull data from database and set up a loop
      TradeVals=DBdata[directory]
      length=len(TradeVals)
   
      # The first loop sums all previous last trades in the database and gets a value that we need for simple linear regression
      for mean_int in range(length):
         summation=summation+TradeVals[mean_int]

         #for simple linear regression we need to calculate the sum of x*y where x is just the integer location of the value in the list.
         #sigxy_sum is part of calcuating the sample covariance
         #We reverse "x" value because array goes from last (latest quote) to first
         sigxy_sum=sigxy_sum+(72-mean_int)*TradeVals[mean_int]

      # Grab the mean trade value by dividing the sum by the amount of entries
      mean=summation/length

      # Bravo is the slope parameter of the simple linear regression model
      # Bravo is the sample covariance divided by the sample variance
      # There is no need to calcuate the estimator so we won't do that
      Bravo=(sigxy_sum-2628*summation/72)/(127020-(2628**2)/72)

      #process another loop to calcuate the sum of variances
      for variance_int in range(length):
         variancesum=variancesum+(TradeVals[variance_int]-mean)**2

      #calcuate the variance by dividing the sum by the amount of entries
      variance=variancesum/(length)

      # calcualte standard deviation 
      standev = variance ** 0.5

      #If the data fits a normal distribution, 95% of the trades should be 2 Standard Deviations from the mean
      # As such, on a normal day 4 SD should be near equivalent to the "threshold" list
      variability=4*standev

      #calcualte the order of magnitude of the last trade
      magnitude=floor(log10(lastvalue))

      # Threshold gives us an event trigger
      # The normal swings of the currencies are $300 for BTC, $20 for ETH, and $0.50 for OMG 
      # If you compare these values to the current prices for the currencies you get the following swings:
      # 4.5% for BTC, 6% for ETH, and 8.4% for OMG
      # These values can be linerized as 8.6% - 1.3% * Magnitude of currency
      # e.g. 8.6% - 1.3% * 3 (BTC) = 4.5%
      # See the beginning of the file is you want hard coded values instead of the formula
      threshold_percent=8.4-1.3*(magnitude)
      threshold=(threshold_percent/100)*lastvalue

      #We are going to say there is a trend if the linear slope projects that trading is outside of the normal (2 SD)
      if (Bravo > ((threshold/2)/72)):
	      trend_str='positive'	
      elif (Bravo < -((threshold/2)/72)):
	      trend_str='negative'	
      else:
	      trend_str='flat'

      #cleaning up text print later
      stdev_str=str(standev)
      vartexttemp = str(variability)
      lastvaluetemp = str(lastvalue)
      highvaluetemp = str(highvalue)
      lowvaluetemp = str(lowvalue)
      thresholdtemp = str(threshold)
      meantemp=str(mean)
      trunc_val=magnitude+4
      lastvalue_str=lastvaluetemp[:trunc_val]
      highvalue_str=highvaluetemp[:trunc_val]
      lowvalue_str=lowvaluetemp[:trunc_val]
      threshold_str=thresholdtemp[:trunc_val]
      mean_str=meantemp[:trunc_val]
      vartext=vartexttemp[:trunc_val]

      payload = ' ' + names[x] + ' movement of: $' + vartext + ' in the last 24hrs. The normal movement is: $' + threshold_str +'\n \nLast trade: $' + lastvalue_str + ' \nThe current trend is: ' + trend_str + '\n \n24hr High: $' +highvalue_str +'\n24hr Low: $' + lowvalue_str + '\n24hr Average: $' + mean_str +' \n ------------'
      message=message + " \n" + payload

   return message



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
        response = "Use the following: \n@cryptobot btc \n@cryptobot eth \n@cryptobot ltc \n@cryptobot omg \n@cryptobot update \n@cryptobot stats"

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

    if command.startswith(GET_STATS):
        response = get_currency_stats()

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
