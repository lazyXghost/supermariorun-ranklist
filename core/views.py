from django.shortcuts import render
import requests
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import time

##################################################
# Variables
# https://docs.google.com/spreadsheets/d/1hfScqSW_y_rl7x1xNWZxUHt0GXWGkpZf2z2EoV6MLSY/edit#gid=1259500772
sheet = pd.DataFrame(pd.read_csv('data'))
details = []
ranklist_updation_time = 30 #minutes
min_problem_rating = 1200
TIME_STAMP=1643913000 #codeforces time stamp for 4th feb 2022
cycle_no = 0
sleepTime = 2 #timeout between codeforces api call
RedListedUsers = [] #users having wrong handle
systemState = "down"
proxy = {'http' : '','https' : ''}
startTime = 0
##################################################

##################################################
# functions to compute data of each user
def removeDuplicates(details):
    x = set()
    res = []
    for _ in details:
        curr_size = len(x)
        x.add(_)
        if len(x) != curr_size:
            res.append(_)
    return res

def get_user_details(handle):
    time.sleep(sleepTime)
    for x in handle.split(" "):
        if len(x):
            handle = x

    user_rating = 0
    rating_api_url = "https://codeforces.com/api/user.info?handles="+handle
    user_rating_json = requests.get(rating_api_url, proxies=proxy).json()
    if(user_rating_json["status"]=="OK"):
        try:
            user_rating = user_rating_json["result"][0]["rating"]
        except:
            pass
    else:
        print("     User rating exception")
        print("     ",rating_api_url, user_rating_json)
        RedListedUsers.append(rating_api_url)

    count = 0
    problem_api_url ="https://codeforces.com/api/user.status?handle="+handle+"&from=1&count=100000"
    user_problem_json = requests.get(problem_api_url, proxies=proxy).json()
    if(user_problem_json["status"]=="OK"):
        problem_set = set()
        for problem in user_problem_json["result"]:
            verdict = problem["verdict"] == "OK"
            problem_time = problem["creationTimeSeconds"]>=TIME_STAMP
            problem_name = problem["problem"]["name"]

            rating = False
            try:
                rating = problem["problem"]["rating"] >= max (user_rating, min_problem_rating)
            except:
                pass

            if (verdict and rating and problem_time):
                problem_set.add(problem_name)
        count = len(problem_set)
    else:
        print("     All Problems exception")
        print("     ",problem_api_url, user_problem_json)
    return [count, user_rating]


def get_all_details():
    global cycle_no, sheet, details,RedListedUsers,systemState
    systemState = "Updating"

    cycle_no += 1
    print("Cycle ",cycle_no)

    RedListedUsers = []
    currentdetails = []
    for i in range(len(sheet)):
        name = sheet.iloc[i]['Name']
        roll_no = sheet.iloc[i]['Roll No*']
        handle = sheet.iloc[i]['Codeforces handle'].split("/")[-1]
        print("Processing", name, "-:")

        user_details = get_user_details(handle)
        print("    ",user_details)

        currentdetails.append((name,roll_no, handle, user_details[0], user_details[1]))
    print(RedListedUsers)
    currentdetails.sort(key=lambda x:x[3], reverse=True)
    details = removeDuplicates(currentdetails)

    systemState = "Sleeping"

def updater():
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_all_details, 'interval', minutes = ranklist_updation_time)
    scheduler.start()
#################################################


#################################################
# funtion to display computed data
def index(req):
    global details, systemState, startTime

    if systemState=="down":
        startTime = time.time()
        get_all_details()

    updateMessage = "Updating"
    if systemState == "Sleeping":
        rem_time = ranklist_updation_time - int((time.time()-startTime)/60)%ranklist_updation_time
        updateMessage += " in "+str(rem_time)+" minutes"

    return render(req, 'core/base.html', {'details': details, "UpdateMessage": updateMessage})
#################################################