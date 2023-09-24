import sys
import asyncio
import json
import requests
from datetime import datetime
from ping3 import ping
from pylitterbot import Account
from pylitterbot.enums import LitterBoxStatus
import pylitterbot
import os

def write_previous_waste_drawer_level_to_file(value, filename="lr_data.txt"):
    with open(filename, "w") as f:
        f.write(str(value))

def read_previous_waste_drawer_level_from_file(filename="lr_data.txt"):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return float(f.read())
    return None

with open("config.json", "r") as f:
    config = json.load(f)

# IP address of litter robot
litter_robot_ip = config["LITTER_ROBOT_IP_ADDR"]

# NotifyMe API access code
access_code = config["NOTIFY_ME_AMAZON_API_KEY"]

# Discord Webhook URL
webhook_url = config["DISCORD_WEBHOOK"]

def sendNotification(message):
    # Prepare the notification message with a date-time stamp
    message_with_time = f'{message} - sent at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'

    # Prepare the request body for Notify Me
    body = json.dumps({
        "notification": message_with_time,
        "accessCode": access_code
    })

    # Send the notification
    response = requests.post(url="https://api.notifymyecho.com/v1/NotifyMe", data=body)

    # Prepare the request body for Discord Webhook
    data = {
        "content": message
    }

    # Send the notification to Discord Webhook
    response = requests.post(url=webhook_url, data=data)

    # Print the response status and content
    print("Body: ", body)
    print("Status Code:", response.status_code)
    print("Response:", response.content)

# Set email and password for initial authentication.
username = config["AUTOPETS_USERNAME"]
password = config["AUTOPETS_PASSWORD"] 
lr_id = config["AUTOPETS_LR_ID"]
fr_id = config["AUTOPETS_FR_ID"]

async def main(run_type):
    # Create an account.
    account = Account()

    try:
        # Connect to the API and load robots.
        await account.connect(username=username, password=password, load_robots=True)

        lr = account.get_robot(lr_id)
        fr = account.get_robot(fr_id)

        print("Litter Robot Is Online: " + str(lr.is_online))
        print("Litter Robot Waste Level: " + str(lr.waste_drawer_level))
        print("Litter Robot Cycle Count: " + str(lr.cycle_count))
        print("Litter Robot Cycle Capacity: " + str(lr.cycle_capacity))
        print("Litter Robot Status: " + str(lr.status))
        print("Litter Robot Status Code: " + str(lr.status_code))
        print("Litter Robot Is Drawer Full Indicator Triggered: " + str(lr.is_drawer_full_indicator_triggered))
        print("Litter Robot Waste Full: " + str(lr.is_waste_drawer_full))
        print("Feeder Robot Online: " + str(fr.is_online))
        print("Feeder Robot Food Level: " + str(fr.food_level))

        if run_type == "daily":
            previous_waste_drawer_level = read_previous_waste_drawer_level_from_file()
            if lr.waste_drawer_level == previous_waste_drawer_level:
                sendNotification("Litter Robot Waste Drawer Level Hasn't Changed Since Yesterday!")
            sendNotification(f"Daily report: {lr.status}, {lr.waste_drawer_level}% full, feeder bot {fr.food_level}% full")
            write_previous_waste_drawer_level_to_file(lr.waste_drawer_level)
        if lr.is_online == False:
            sendNotification("Litter Robot is Offline!")
        if lr.waste_drawer_level > 95:
            sendNotification("Litter Robot Is Nearly Full!")
        #if lr.is_waste_drawer_full == True:
        #    sendNotification("Litter Robot Is Totally Full!")
        if lr.status != LitterBoxStatus.READY:
            sendNotification(f"Litter Robot Status Code Fault: {lr.status}")
        if fr.is_online == False:
            sendNotification("Feeder Robot Is Offline!")
        if fr.food_level < 5:
            sendNotification("Feeder Robot Is Nearly Empty!")

    finally:
        # Disconnect from the API.
        await account.disconnect()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: python autopetsisdown.py [hourly|daily]")
        sys.exit(1)

    if sys.argv[1] == "hourly":
        # Do hourly task
        print("Performing hourly task...")
    elif sys.argv[1] == "daily":
        # Do daily task
        print("Performing daily task...")
    else:
        print("Invalid argument. Usage: python script.py [hourly|daily]")
        sys.exit(1)

    if ping(litter_robot_ip) == None:
        print('Ping to Litter Robot Failed!')
        sendNotification("Litter Robot Is Offline!")

    asyncio.run(main(sys.argv[1]))











