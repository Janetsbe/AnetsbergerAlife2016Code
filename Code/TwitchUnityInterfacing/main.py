#Code used and modified with permission from author. From: http://pastebin.com/xxWb6Rzg. 
#Original author: Frederik Witte http://www.wituz.com/
#Code acquired on 9/02/2015


# Main driver for TPEvoRobots (twitch plays evolutionary robotics). Makes calls to connect to twitch.tv's IRC chat and receive chat messages.
# Controls flow of execution for c#/unity program running robots. Makes calls to write to DB to store
# robot data and pass messages to c#/unity. We define the following terms:
# Instance run: a run containing a specific instance of a robot with a unique controller, not necessarily unique body or command.
# Command run: a run containing one or more instance runs under one command.
# Robot type run: a run containing one or more command runs where the body of the robot is kept consistent.
# These three types of runs are to have set durations such that duration_instance <= duration_command <= duration_robottype.
# For experiment purposes, an instance will be set to one minute, a new command run beginning every 3 minutes, and a new body every hour.

import twitch;
import datetime;
import random;
import math;
import os;
import time;
import database;
import subprocess;

#define durations in seconds
INSTANCE_DURATION = 30;
COMMAND_DURATION_NONE = INSTANCE_DURATION;
COMMAND_DURATION_HAS_COMMAND = INSTANCE_DURATION * 6;
ROBOT_TYPE_DURATION = INSTANCE_DURATION * 120;

BACKUP_INTERVAL = 40 * 60; #seconds. Interval for full DB backup


#Function which generates a valid reinforcement signal (RS) given the current robot's color and the immediately
#previous robot's color.  This is done such that "late" incoming RS can be tied to the correct robot.
def generateValidRewards(curColor, prevColor):

    validRS = [curColor[0] + "y", curColor[0] + "n"];
    if(not(prevColor == None)):
        validRS.append(prevColor[0] + "y");
        validRS.append(prevColor[0] + "n");

    return validRS;
  
#Shortcut to getting a deltatime object.
def getDeltaTime(seconds):
    return datetime.timedelta(seconds = seconds);

#Makes calls to db object's "messages" collection, which passes messages used by the unity program.
def writeRobotValues(command, controller, color, robotType, robotID, validRS):

    db.setMessage("color", color);
    db.setMessage("controller", controller);
    db.setMessage("command", command);
    db.setMessage("robotType", robotType);
    db.setMessage("robotID", str(robotID));
        
#Generates a random open loop controller. Returns a 2d array, C_ij, where i is a robot's joint and j is one of the three
#coefficients of a sin function to be used in robot joint actuation (amplitude, period, and phase offset respectively).
#ranges for random generation are selected to function as-is where joint actuation is a function of the unity
#program's current time step. Specific ranges were observed to generate robots which perform a reasonable variety of
#behaviors without being consistently erratic or overly energetic but still varying from slow moving to flipping/leaping.
#Note that all controllers are recorded with their respective robot's data and may be re-run due to unity's deterministic physics
#should there be a need.
def generateController(robotType):
    numJoints = 2 if robotType == "simple" else 6;
    controller = [];
    for i in range(0, numJoints):
        controller.append([]);

        controller[i].append(random.uniform(.6, 1.5)); #amplitude
        controller[i].append(random.uniform(.01, .09)); #period
        controller[i].append(random.uniform(- 10 * math.pi, 10 * math.pi)); #phase offset
    # print(controller);  
    return controller;

#Returns a value representing whether a string is a valid RS.
def isRewardSignal(string):
    return string in validRewardSignals;

#shortcut for datetime.datetime.now()
def now():
    return datetime.datetime.now();


#Checks if string is a "command". 
#This is determined by the following conditions:
#   - the string must be shorter than 30 characters.
#   - the string must be longer than two characters.
#   - the string must not contain "http" (to prevent links from being displayed in the unity GUI by spammers)
def isCommand(string):
    condition1 = len(string) <= maxCommandLength and len(string) > 2;
    condition2 = "http" not in string;
    #print(condition1 and condition2)
    return condition1 and condition2;

#Returns a deltatime object representing the difference between two times, time1 and time2.
def timeBetween(time1, time2):
    return time1 - time2;

#Calls the DB class's write methods to send a message to the unity program corresponding to the remaining
#amount of time for the current instance and command runs.
def sendTimerMessages(instanceTimer, commandTimer, instanceDuration, commandDuration):

    instanceTimeLeft = instanceDuration - instanceTimer;
    instanceTimeLeftString = str(instanceTimeLeft.seconds) + "." + str(instanceTimeLeft.microseconds)[0:2];
    commandTimeLeft = commandDuration - commandTimer;
    commandTimeLeftString = str(commandTimeLeft.seconds) + "." + str(commandTimeLeft.microseconds)[0:2];
    # print("instance Time left : " + instanceTimeLeftString);
    # print("command Time left : " + commandTimeLeftString);
    db.setMessage("instanceTimeLeft", instanceTimeLeftString);
    db.setMessage("commandTimeLeft", commandTimeLeftString);


lastBackup = now(); 
db = database.database("tpevorobots");


#Initialize variables to be used.
maxCommandLength = 30;
robotType = "";
validColors = ["blue", "orange", "violet"];


# Place moderator/researcher's names here to allow them to interact with 
# twitch chat without having their input be read by the simulation.
filteredUsers = ["moderator1", "experimenter0", "janetsbe", "etc, etc, etc"]; 


curColorIndex = 0;
previousRobotColor = None;
robotColor = None;
validRewardSignals = []

commandVotes = {};

#None is the "default" command representing the fact that the robot has not been given a command
currentCommand = "none";

#Initialize the current instance ID, to be re-set properly by querying the database for the next actual ID to be used.
curInstanceID = 0;

reward = 0;
punish = 0;

controller = [];
instanceDuration = getDeltaTime(INSTANCE_DURATION);
commandDuration = getDeltaTime(COMMAND_DURATION_NONE);
robotDuration = getDeltaTime(ROBOT_TYPE_DURATION);
db.setMessage("nextRobot", True);

newRobot = True;
newController = True;
newCommand = True;

robotTypeStartTime = None;
commandStartTime = None;
instanceStartTime = None;



t = twitch.Twitch();


#Enter your twitch username and oauth-key below, and the app connects to twitch with the details.
#Your oauth-key can be generated at 
username = ""; #Your twitch username. ALL LOWER CASE
key = ""; #Key acquired from twitch.tv account page
t.twitch_connect(username, key);
 

rawChatMessages = [] 
running = True;

db.setMessage("nextRobot", True);

#The main loop
while running:

    currentTime = now();

    if(newController):
        instanceStartTime = currentTime;  
        db.addChatMessages(rawChatMessages);
        rawChatMessages = [];
        print("new controller")
        previousRobotColor = robotColor;
        robotColor = validColors[curColorIndex % len(validColors)];
        curColorIndex += 1;
        validRewardSignals = generateValidRewards(robotColor, previousRobotColor);

        if(newCommand):
            print("new command")

            command = db.getMostCommonCommand();
            if(newRobot):
                print("new robot")
                robotTypeStartTime = now();
                robotType = "complex" if (robotType == "simple") else "simple"; #simply alternating between two robot morphologies in this iteration
                newRobot = False;
                command = "none";   
            #end if(newRobot)

            db.clearVoteData();
            db.sendMostCommonVotes(3);
            print(validRewardSignals)
            db.newCommandRun();
            commandStartTime = now();
            newCommand = False;
        #end if(newCommand)

        db.newControllerRun(validRewardSignals);
        reward = 0;
        punish = 0;
        commandDuration = getDeltaTime(COMMAND_DURATION_HAS_COMMAND) if (command != "none") else getDeltaTime(COMMAND_DURATION_NONE);
        curInstanceID = db.nextID();
        newController = False;
        db.setMessage("reward", 0);
        db.setMessage("punish", 0);
        controller = generateController(robotType);



        writeRobotValues(command, controller, robotColor, robotType, curInstanceID, validRewardSignals);

       
        db.addRobotInstance(str(curInstanceID), robotType, robotColor, instanceStartTime, controller, command);
        print("New instance of a robot such that: \n   Robot Type: " + robotType 
            + "\n   Robot Color: " + robotColor
            + "\n   Previous Color: " + str(previousRobotColor)
            + "\n   Instance ID: " + str(curInstanceID) + "\n   Command: " + command 
            + "\n   Robot Start Time: " + str(instanceStartTime)
            + "\n   Valid reward signals: " + str(validRewardSignals));


    instanceTimer = timeBetween(currentTime, instanceStartTime);
    commandTimer = timeBetween(currentTime, commandStartTime);

    sendTimerMessages(instanceTimer, commandTimer, instanceDuration, commandDuration);

    ##########################################################################################################
    # Code above deals with setting up appropriate robot data for unity.
    #
    # Code below deals with interfacing with twitch
    ##########################################################################################################

    #Check for new messages
    newMessages = t.twitch_recieve_messages(amount = 1024);

    if newMessages:

        for message in newMessages:

            #Try block, some characters are not understood by python and can cause exceptions
            try:
                #Get info from message.
                msg = str(message['message'].lower());
                username = str(message['username'].lower());
                print(username + ": " + msg);

                rawChatMessages.append((username, currentTime, msg));

                if(username not in filteredUsers):
 
                    if(msg in validRewardSignals[0:2]):
                        if(msg[1] == 'y'):
                            reward += 1;
                        else:
                            punish += 1;
                        db.addRewardSignal(curInstanceID, msg, username, now());
                        
                        db.setMessage("rewardUserQueue", username + ":" + msg, setType = "$push");

                        db.setMessage("reward", reward);
                        db.setMessage("punish", punish);


                    elif(len(validRewardSignals) > 2 and msg in validRewardSignals[2:4]):
                        db.addPreviousRewardSignal(curInstanceID - 1, msg, username, now());


                    elif isCommand(msg):
                        db.addCommandVote(curInstanceID, msg, username, now());
                        
                        db.setMessage("commandUserQueue", username + ":" + msg, setType = "$push");
            
                        db.sendMostCommonVotes;

            except:
                print("msg error")
                #end if not in filtered users
        #end for each message in new messages
    #end if new messages


    if(instanceTimer >= instanceDuration):
        if(commandTimer >= commandDuration):
            #command = db.getMostCommonCommand();
            newCommand = True;
            if(timeBetween(currentTime, robotTypeStartTime) >= robotDuration):
                print("time for a new robot");
                newRobot = True;
        
        print("   Robot end time: " + str(now()));
        db.setMessage("nextRobot", True);
        newController = True;
        db.endRobot(curInstanceID, now());

        print("=======================" + str(timeBetween(now(), lastBackup)));
        if(timeBetween(now(), lastBackup) > datetime.timedelta(seconds = BACKUP_INTERVAL)):
            print("-Backing up database- - -" + str(timeBetween(lastBackup, now())));
            db.backupData();
            lastBackup = now();

    #end if instance timer
#end main program loop

for element in rawChatMessages:
    print(element);

