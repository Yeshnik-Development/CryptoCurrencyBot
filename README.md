# CryptoCurrencyBot
A Slack bot that pulls data from the GDAX API

## Setup:

To setup a slackbot, you need to follow the first steps here: https://www.fullstackpython.com/blog/build-first-slack-bot-python.html

You need to work through the webpage until you reach the "Coding Our StarterBot" point on that webpage.
At that point you should have the slackbot ID and the slackbot token

## AutoRun:

I designed this bot to run on a raspberry pi that is running Raspberrian. If you are using the same I suggest using a shell script to startup the python script at startup. This can easily be done by adding the following command to crontab:

@reboot bash /home/pi/Development/pythonstarter.sh

A copy of pythonstarter.sh is included in the main branch. You may also need to change the permission of the file (chmod +x)

Additionally, there is a sleep command include in the pythonstarter.sh file. The command is necessary if cron starts early in the boot (which prevents the python script from working properly if your network adapter has not been initalized)

