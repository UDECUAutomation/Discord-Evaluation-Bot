import discord_evals as deval
import json
import os
import openai
import discord
import discord_evals as d_eval
import requests
import threading
import pandas as pd

openai.api_key = "KEY"

# eventHandler.py

token = 'TOKEN'

# load_dotenv()
#TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents = intents)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_ready():
    print("Logged in as a bot {0.user}".format(client))
    #print(await compare_thread())
    
async def compare_thread():
    thread_id = ""
    submission = d_eval.get_latest_submission()
    given_name = submission["Candidate's Name"]
    #given_name = input
    channel = client.get_channel(1065448943892299856)
    for thread in channel.threads:
        print(thread.name)
        if given_name in thread.name:
            thread_id = thread.id
            thread_current = thread
            break
    if thread_id == "":
        await create_thread(given_name)
    else:
        # Matt - Figure out how to read the contents of the last message to compare timestamps
        # if submission["Timestamp"] in thread_current.last_message.content
        await thread_current.send(embed=message_payload())

def message_payload():
    data = d_eval.get_latest_submission()
    if "0 - Unsatisfactory" in data["Base Points"]:
        color = 0xff1100
    elif "0 - Experience Only" in data["Base Points"]:
        color = 0xffbb00
    elif "2 - Satisfactory" in data["Base Points"]:
        color = 0x00ff0d
    elif "3 - Satisfactory" in data["Base Points"]:
        color = 0x0059ff
    else:
        color = 0x919191
    #Block 1
    critique_info = ""
    critique_info += "Date of Evaluation: " + str(data.get("Date")) + "\n"
    critique_info += "Submitted by: " + str(data.get("FTO's Name")) + " (" + str(data["FTO's Email"]) + ")" + "\n"
    critique_info += "Candidate's Name : " + str(data.get("Candidate's Name")) + " (" + str(data["Candidate's Email"]) + ")" + "\n"
    critique_info += "**FTO's Comments: **" + str(data.get("FTO's Comments")) + "\n"
    critique_info += "Candidate's Comments: " + str(data.get("Candidate's Comments")) + "\n"
    critique_info += "Training Phase: " + str(data.get("Training Phase")) + "\n"
    critique_info += "Base Points: " + str(data.get("Base Points")) + "\n"
    critique_info += "Total Points: " + str(data.get("Total Points")) + "\n"

    
    embedVar = discord.Embed(title="UDECU Field Critique Form", description="EMS Field Training Evaluation for " + data["Candidate's Name"] + " by "+ data["FTO's Name"] + "\n" + critique_info, color=color)
    embedVar.add_field(name="Critique Information", value=critique_info, inline=False)
    return embedVar

async def create_thread(name):
    channel = client.get_channel("Channel ID")
    #print(channel.threads)
    thread = await channel.create_thread(name=name,type=discord.ChannelType.public_thread)
    print(thread.id)
    return await thread.send(embed=message_payload()) #dont fucking touch