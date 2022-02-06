from django.shortcuts import render
import requests
import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import time

##################################################
# Variables
# https://docs.google.com/spreadsheets/d/1hfScqSW_y_rl7x1xNWZxUHt0GXWGkpZf2z2EoV6MLSY/edit#gid=1259500772
sheet = pd.DataFrame(pd.read_csv('data'))
details = {}
ranklist_updation_time = 15 #minutes
min_problem_rating = 1200
TIME_STAMP=1643913000 #codeforces time stamp for 4th feb 2022
cycle_no = 0
sleepTime = 2 #timeout between codeforces api call
RedListedUsers = [] #users having wrong handle
systemState = "down"
proxy = {'http' : '','https' : ''}
startTime = 0
lastContestId = 1633
development = False
##################################################

##################################################
# functions to compute data of each user
if development:
    sleepTime = 0

# def removeDuplicates(y):
#     x = set()
#     res = []
#     for _ in y:
#         curr_size = len(x)
#         x.add(_)
#         if len(x) != curr_size:
#             res.append(_)
#     return res

def get_questions(handle, rating):
    time.sleep(sleepTime)

    count = 0
    problem_api_url ="https://codeforces.com/api/user.status?handle="+handle+"&from=1&count=100000"
    problem_json = requests.get(problem_api_url, proxies=proxy).json()
    if(problem_json["status"]=="OK"):
        problem_set = set()
        for problem in problem_json["result"]:
            verdict = problem["verdict"] == "OK"
            problem_time = problem["creationTimeSeconds"]>=TIME_STAMP
            problem_name = problem["problem"]["name"]

            rating = False
            try:
                rating = problem["problem"]["rating"] >= max (rating, min_problem_rating)
            except:
                pass

            if (verdict and rating and problem_time):
                problem_set.add(problem_name)
        count = len(problem_set)
    else:
        print("     All Problems exception")
        print("     ",problem_api_url, problem_json)
    return count


def get_all_details():
    global cycle_no, sheet, details,RedListedUsers,systemState

    systemState = "Updating"
    cycle_no += 1
    print("Cycle ",cycle_no)

    RedListedUsers = []
    for i in range(len(sheet)):
        name = sheet.iloc[i]['Name']
        roll_no = sheet.iloc[i]['Roll No*']

        print(str(i+1)+"."+name+"-:")
        temp = sheet.iloc[i]['Codeforces handle'].split("/")[-1].split(" ")
        if len(temp)>2:
            handle = ""
        else:
            if len(temp[0]):
                handle = temp[0]
            else:
                handle = temp[1]

        rating = 0
        rating_api_url = "https://codeforces.com/api/user.rating?handle="+handle
        rating_json = requests.get(rating_api_url, proxies=proxy).json()
        if(rating_json["status"]=="OK"):
            for contest in rating_json["result"]:
                try:
                    if(contest["contestId"]<=lastContestId):
                        rating = contest["newRating"]
                except:
                    pass
            try:
                questions = get_questions(handle, rating)
            except:
                questions = 0
            print("    Rating-:",rating)
            print("    Questions-:",questions)
        else:
            handle = "WRONG HANDLE -:"+sheet.iloc[i]['Codeforces handle']
            rating = -1
            questions = -1

            print("     Wrong handle")
            print("    ",rating_api_url, rating_json)
            RedListedUsers.append((name, roll_no))

        details[roll_no] = (name,roll_no, handle, rating, questions)
    print(RedListedUsers)
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

    print("SystemState", systemState)
    updateMessage = "Updating"
    if systemState == "Sleeping":
        rem_time = ranklist_updation_time - int((time.time()-startTime)/60)%ranklist_updation_time
        updateMessage += " in "+str(rem_time)+" minutes"

    currentdetails = []
    for key in details:
        currentdetails.append(details[key])
    currentdetails.sort(key=lambda x:(x[4],x[3]), reverse=True)
    # currentdetails = removeDuplicates(currentdetails)

    return render(req, 'core/base.html', {'details': currentdetails, "UpdateMessage": updateMessage})
#################################################
