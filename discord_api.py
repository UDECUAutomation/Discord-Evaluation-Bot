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
    
#Interactive Discord Eval Bot
@client.event
async def on_message(message):
    print(message)
    #relevant functions
    
    def get_submission_for(name):
        SHEET_ID = "SHEET ID"
        SHEET_NAME = "SHEET NAME"
        url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
        df = pd.read_csv(url)
        length = len(df.index)
        name_dic = []
        name1 = str(name).lower()
        d1 = df["Candidate's Name"].str.lower()
        for row in range(0,len(d1.index)):
            if name1 in d1[row]:
                name_dic.append(df.values[row])
        dataframe = pd.DataFrame(name_dic, columns=df.keys())
        return dataframe

    async def eval_report(message):
        if "eval_report" in message.content.lower():
            name = str(message.content.lower().replace("eval_report ", "")).title()
            name1 = name.lower()
            print(name1)
        if "my_report" in message.content.lower():
            name = message.author.nick
            name1 = name.lower()
            print(name1)
        data = get_submission_for(name1)
        if len(data.index) > 0:
            #Descriptive Stats
            x=0
            elig_data = data.loc[data['Base Points'].isin(["2 - Satisfactory Transport/Refusal", "0 - Unsatisfactory/No Patient Contact/No Assessment Made", "3 - Satisfactory Priority Call (Assessment made, intervention performed)"])]
            if len(elig_data.index) <= 10:
                x = sum(elig_data["Total Points"])
                ten_pass_rate = x/(len(elig_data.index)*2)*100
            else:
                x= sum(elig_data["Total Points"].iloc[0:10])
                ten_pass_rate = x/20*100
            ten_pass_rate_per = str(ten_pass_rate) + "%"
            point_count = sum(data["Total Points"])
            current_phase = ""
            if "Evaluation" in data["Training Phase"].values:
                current_phase = "Evaluation"
            elif "Instruction" in data["Training Phase"].values:
                current_phase = "Instruction"
            elif "Observation" in data["Training Phase"].values:
                current_phase = "Observation"

            recent_evals_dic = []
            
            if len(data.index) >3:
                for i in range(0,3):
                    recent_evals_dic.append(str(data["Date"][i])+ " " +str(data["FTO's Name"][i]))
                recent_evals = "\n".join(recent_evals_dic)
            else:
                for i in range(0,len(data.index)):
                    recent_evals_dic.append(str(data["Date"][i])+ " " +str(data["FTO's Name"][i]))
                recent_evals = "\n".join(recent_evals_dic)

            recent_prompt_dic = []
            for i in range(0,len(data.index)):
                if data["Summarized Prompts"].isnull()[i] == True :
                    continue
                else:
                    recent_prompt_dic.append(str(data["Summarized Prompts"][i]))
            rec_prompt_parsed = recent_prompt_dic[0:5]
            recent_prompt = "\n".join(rec_prompt_parsed)

            #Obs Criteria
            two_obs_calls = bool
            if len(data["Base Points"] == "0 - Experience Only") >= 2:
                two_obs_calls = True
            else: two_obs_calls = False
            if two_obs_calls == True: obs_criteria="Complete"
            else: obs_criteria = "Incomplete"
            
            #Inst Criteria
            thirty_points = bool
            eighty_pass = bool
            inst_criteria = ""
            if sum(data["Total Points"]) >= 30: thirty_points = True
            else: thirty_points = False
            if ten_pass_rate >=80: eighty_pass = True
            else: eighty_pass = False
            if current_phase == "Evaluation":
                inst_criteria = "Complete"
                eighty_pass = True
                thirty_points = True
            elif thirty_points == True and eighty_pass == True:
                inst_criteria="Complete"
            elif thirty_points == True or eighty_pass == True: 
                inst_criteria="Partial"
            elif thirty_points == False and eighty_pass == False: 
                inst_criteria = "Incomplete"

            #Eval Criteria
            twenty_points = bool
            eighty_pass = bool
            priority = bool
            prior_data = data[data["Base Points"] == "3 - Satisfactory Priority Call (Assessment made, intervention performed)"]
            type_prior_data_dic = []
            points_data = data[data["Training Phase"] == "Evaluation"]
            for i in prior_data.index:
                type_prior_data_dic.append(str(prior_data["Select those that apply"][i]))
            priority_types = ", ".join(type_prior_data_dic)
            eval_points = sum(points_data["Total Points"])

            if eval_points >= 20: twenty_points = True
            else: twenty_points = False
            if ten_pass_rate >=80: eighty_pass = True
            else: eighty_pass = False
            if len(prior_data.index) >= 2 and "Trauma" in prior_data["Select those that apply"].values: priority = True
            else: priority = False
            if twenty_points == True and eighty_pass == True and priority == True: eval_criteria="Complete"
            elif twenty_points == True or eighty_pass == True or priority == True: eval_criteria="Partial"
            else: eval_criteria = "Incomplete"

            #FP Criteria
            ten_points = bool
            five_pass = bool
            priority1 =  bool
            fp_list = []
            five_pass_rate = str(sum(elig_data["Total Points"].iloc[0:5])/10*100) + "%"

            if len(prior_data.index) >= 1: priority1 = True
            else: priority1 = False
            if sum(elig_data["Total Points"].iloc[0:5])/10*100 >= 80:
                five_pass = True
            else: five_pass = False
            if eval_points > 10:
                ten_points = True
            else: ten_points = False
            if current_phase != "Evaluation":
                fp_crit = "Ineligible"
            else:
                if ten_points == True and five_pass == True and priority1 == True:
                    fp_list.append("Eligible")
                if priority1 == False:
                    fp_list.append("Awaiting Priority")
                if five_pass == False:
                    fp_list.append(f"Awaiting 5-Call Pass Rate to 80%, currently {five_pass_rate}")
                if ten_points == False:
                    fp_list.append("Awaiting 10 points in Eval")
                fp_crit = ", ".join(fp_list)

            #color of message
            if current_phase == "Observation":
                if obs_criteria == "Complete":
                    color = 0x2AFF00
                else:
                    color = 0xFF0000
            elif current_phase == "Instruction":
                if inst_criteria == "Complete":
                    color = 0x2AFF00
                elif inst_criteria == "Partial":
                    color = 0xFFAC00
                elif inst_criteria == "Incomplete":
                    color = 0xFF0000
            elif current_phase == "Evaluation":
                if eval_criteria == "Complete":
                    color = 0x2AFF00
                elif eval_criteria == "Partial":
                    color = 0xFFAC00
                elif eval_criteria == "Incomplete":
                    color = 0xFF0000
            else:
                color = 0xAFAFAF

            embedVar = discord.Embed(title="Eval Report for " + str(name), description=f"""
            **__Descriptive Stats:__**
            **Current Eval Phase:** {current_phase}
            **# of Points:** {point_count}
            **Pass Rate (10):** {ten_pass_rate_per}
            **Recent Evals (3):** \n{recent_evals}\n
            **Recent Prompts (5):** \n{recent_prompt}
            """,
            color=color)
            embedVar.add_field(name="__Obs Criteria__", value=f"""
            **Two Observation Calls Met?** {two_obs_calls}
            **Observation Criteria:** {obs_criteria}
            """,
            inline=False)
            embedVar.add_field(name="__Inst Criteria__", value=f"""
            **30 Points Requirement Met?** {thirty_points}
            **80% Pass Rate Met?** {eighty_pass}
            **Instruction Criteria:** {inst_criteria}
            """,
            inline=False)
            embedVar.add_field(name="__Eval Criteria__", value=f"""
            **20 Points in Eval Requirement Met?** {twenty_points}
            **# of Eval Points:** {eval_points}
            **80% Pass Rate Met?** {eighty_pass}
            **Med&Trauma Priorities Met?** {priority}
            **Priority Calls Passed:** {priority_types}
            **Evaluation Criteria:** {eval_criteria}
            """,
            inline=False)
            embedVar.add_field(name="__FP Criteria__", value=f"""
            **FP Eligibility** = {fp_crit}
            """,
            inline=False)
            if "my_report" in message.content.lower():
                await discord.User.send(self=message.author, embed=embedVar)
                await message.delete()
            else:
                await message.channel.send(embed=embedVar)
        else: await message.channel.send("No Evals Found. Check Name Spelling & Google Sheet Filters.")
    
    if ((message.channel.name == "board-of-techs"  or message.channel.name == "candidate-reports" or message.channel.name == "test2" or message.channel.name == "field-training-progress" or message.channel.name == "openai") and ("eval_report" in message.content.lower() or "my_report" in message.content.lower()) and (message.author.bot == False)):
        await eval_report(message)

def start():
    client.run(token)

start()
