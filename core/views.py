from os import system
from django.shortcuts import render
import requests
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import time

##################################################
# Variables
systemState = "sleeping"
sheet = pd.DataFrame(pd.read_csv('data'))
details = []
ranklist_updation_time = 20 #minutes
min_problem_rating = 1200
TIME_STAMP=1643913000 #codeforces time stamp for 4th feb 2022
cycle_no = 0
sleepTime = 2
RedListedUsers = []
RedListedProblems = []
proxy = {'http' : '','https' : ''}
##################################################

##################################################
# functions to compute data of each user
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
        RedListedProblems.append(problem_api_url)
    return [count, user_rating]


def get_all_details():
    global cycle_no, sheet, details,RedListedUsers,RedListedProblems,systemState
    cycle_no+=1
    print("Cycle ",cycle_no)

    RedListedUsers = []
    RedListedProblems = []
    currentdetails = []
    for i in range(len(sheet)):
        name = sheet.iloc[i]['Name']
        roll_no = sheet.iloc[i]['Roll No*']
        handle = sheet.iloc[i]['Codeforces handle'].split("/")[-1]
        print("Processing", name, "-:")

        user_details = get_user_details(handle)
        print("    ",user_details)

        if(systemState == "working"):
            details.append((name,roll_no, handle, user_details[0], user_details[1]))
            details.sort(key=lambda x:x[3], reverse=True)

        currentdetails.append((name,roll_no, handle, user_details[0], user_details[1]))
    print(RedListedUsers)
    print(RedListedProblems)
    currentdetails.sort(key=lambda x:x[3], reverse=True)
    details = currentdetails
    # return redirect('/')

def updater():
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_all_details, 'interval', minutes = ranklist_updation_time)
    scheduler.start()
#################################################


#################################################
# funtion to display computed data
def index(req):
    global details, systemState
    if systemState=="sleeping":
        systemState = "working"
        get_all_details()
        systemState = "up"
    return render(req, 'core/base.html', {'details': details})
#################################################