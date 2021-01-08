'''
Discord Alert Bot

Author: Jarrod Carson
'''

# ==============================IMPORTS===============================
import asyncio
import datetime as dt
import discord 
from discord.ext.commands import Bot
from discord.ext import tasks
from pytz import timezone
from replit import db
from os import getenv
from alert import Alert

# ==============================GLOBALS===============================
bot = Bot('$')
loop = asyncio.get_event_loop()

# Channels the bot uses to communicate 
input_channel = "bot-commands"
alert_channel = "test-channel-1"
review_channel = "test-channel-2"

# Repl servers do not use the same timezone so it must be manually set
tz = timezone("US/Central")

wip_alerts = {}


# ==============================EVENTS================================
@bot.event
async def on_ready():
  '''
  Function called when the bot successfully logs on
  '''
  await bot.change_presence(
    activity=discord.Game(name="Keeping you alert"))
  print("Online: Connected on {0}".format(dt.datetime.now(tz)))

  if "Alerts" not in db:
    db["Alerts"] = []

  db["Channels"] = [input_channel, alert_channel, review_channel]

  # DEBUG Statement. Remove from release
  db["Alerts"] = []


@bot.command()
async def cancel(ctx):
  '''
  Cancels an in-progress alert by a user
  '''
  if ctx.author in wip_alerts:
    del wip_alerts[ctx.author]


@bot.command()
async def new_alert(ctx):
  '''
  Handles new alert commands
  '''
  if ctx.channel != db["Channels"][0]:
    print(1)
    return
  if ctx.author not in wip_alerts:
    wip_alerts[ctx.author] = {"step": 0, "alert": [], 
                              "name": str(ctx.author), "time_since_last_update": 0.0}
    await message_user(ctx, wip_alerts[ctx.author])
  else:
    await ctx.channel.send("You are already creating an alert.")


@bot.event
async def on_message(message):
  '''
  Handles all message events, e.g. alert construction
  '''
  if isinstance(db["Channels"][0], str):
    db["Channels"][0] = discord.utils.get(message.guild.channels, name=input_channel)
    db["Channels"][1] = discord.utils.get(message.guild.channels, name=alert_channel)
    db["Channels"][2] = discord.utils.get(message.guild.channels, name=review_channel)

  if message.author == bot.user:
    return

  if message.author in wip_alerts and str(message.channel).find(str(message.author)):
    wip_alerts[message.author]["alert"].append(message.content)
    wip_alerts[message.author]["step"] += 1
    await message_user(message, wip_alerts[message.author])

  await bot.process_commands(message)


# ============================EVENT HELPERS===========================
async def message_user(ctx, user):
  '''
  Dynamically prompts users for parts of the alert
  '''
  prompts = [
    "Hey {0}! I see you're trying to create an alert. I'll just be asking you to provide some info to get it set up.\n\n".format(str(ctx.author).split('#')[0]) +
    "-" * 100 + "\n\n",

    "```First part: What should the subject/title of your alert be?\n\n" +
    "Ex. 'Data Structures Final Exam'\n```",

    "```Second part: Write up a short little description describing the alert (1000 character limit)\n\n" +
    "Note: Enter a single period '.' to skip the description\n```",

    "```Third part: What day do you want the alert to show on?\n\n" +
    "Note: Please enter in the format mm-dd-yyyy. Ex. 02-10-2021\n```",

    "```Final part: What time do you want the alert to show?\n\n" +
    "Note: Please enter in the format HH:MM and in 24-hour format. Ex. 4:00 pm would be 16:00\n```"
  ]

  if user["step"] <= 4:
    if user["step"] == 0:
      await ctx.author.send(prompts[user["step"]] + prompts[user["step"] + 1])
      user["step"] += 1
    else:
      await ctx.author.send(prompts[user["step"]])

  elif user["step"] == 5:
    alert_draft = "```**AUTHOR**: {0}\n\n".format(str(ctx.author)) +\
                  "**SUBJECT**: {0}\n\n".format(user["alert"][0]) +\
                  "**DESCRIPTION**: {0}\n\n".format(user["alert"][1]) +\
                  "**DATE & TIME**: {0}, {1}```".format(user["alert"][2], user["alert"][3])

    await ctx.author.send("Alright here's what I have so far:\n" + alert_draft +
                          "If this looks good enter 'y' to submit it\n")
  else:
    if user["alert"][4].lower() == 'y':
      await ctx.author.send("Alert has been submitted for approval")
      await create_alert(user)
      del user


async def create_alert(user):
  '''
  Creates a scheduled alert from user input
  '''

  alert = Alert(user["name"], user["alert"][0], user["alert"][1],
                user["alert"][2], user["alert"][3])

  db["Alerts"].append(alert)


@tasks.loop(seconds=5)
async def check_alerts():
  '''
  Posts an alert if the date and time conditions are met
  '''
  if not db["Alerts"]:
    return

  alert = db["Alerts"][0].get_attr()

  date = dt.datetime.now(tz).strftime("%m-%d-%y")
  time = dt.datetime.now(tz).strftime("%H:M")

  if alert["date"] < date:
    db["Channels"][1].send("```**AUTHOR**: {0}\n\n".format(alert["author"]) +\
                           "**SUBJECT**: {0}\n\n".format(alert["subject"]) +\
                           "**DESCRIPTION**: {0}\n\n".format(alert["desc"]) +\
                           "**DATE & TIME**: {0}, {1}```".format(alert["date"], alert["time"]))
    db["Alerts"].pop(0)
  if alert["date"] == date:
    if alert["time"] <= time:
      db["Channels"][1].send("```**AUTHOR**: {0}\n\n".format(alert["author"]) +\
                             "**SUBJECT**: {0}\n\n".format(alert["subject"]) +\
                             "**DESCRIPTION**: {0}\n\n".format(alert["desc"]) +\
                             "**DATE & TIME**: {0}, {1}```".format(alert["date"], alert["time"]))
      db["Alerts"].pop(0)


# =============================MAIN LOOP==============================
async def mainloop():
  
  await bot.start(getenv("TOKEN"))


if __name__ == "__main__":
  loop.run_until_complete(mainloop())
