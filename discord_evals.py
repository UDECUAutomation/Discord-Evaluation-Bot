import pandas as pd
import gspread
import json
import requests
import threading
import time

#reads google sheets
SHEET_ID = "SHEET ID"
SHEET_NAME = "SHEET NAME"

url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
df = pd.read_csv(url)

#local
def get_latest_submission():
    while True:
        dic ={}
        for key in df.keys():
            dic[key] = df.get(key)[0]
        return dic

def get_all_submission():
    dic ={}
    length = len(df.index)
    for row in range(0,len(df.index)):
        for key in df.keys():
            dic[key+str(row)] = df.get(key)[row]
    return [dic, length]

def get_submission_for(name):
    length = len(df.index)
    name_dic = []
    name1 = str(name).lower()
    d1 = df["Candidate's Name"].str.lower()
    for row in range(0,len(d1.index)):
        #print(df.get("Candidate's Name")[row])
        #print(row)
        #if name1 in df.get("Candidate's Name")[row]:
        if name1 in d1[row]:
            name_dic.append(df.values[row])
            #print(name)
    dataframe = pd.DataFrame(name_dic, columns=df.keys())
    return dataframe


        


def start():
    threading.Thread(target=get_latest_submission).start()