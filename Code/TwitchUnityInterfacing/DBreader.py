from pymongo import MongoClient;
from datetime import datetime;
from datetime import date;
import math
from bson.json_util import dumps
import operator;
import subprocess;


#handles reading from mongoDB datase and formatting data structures appropriately for 
#storing data external to any running simulation
class DBreader:

	def __init__(self):
		self.client = MongoClient();
		self.db = self.client.tpevorobots;
		self.data = self.db.robotdata;
		self.chatLog = self.db.rawChatLog;


	def getRobotData(self, robotType = "all", command = None, minRS = 1, fromTime = datetime(2000, 1, 1, 0, 0, 0, 0) , 
					 toTime = datetime.now(), robotID = "all"):
		commandFilter = {"$ne": None} if (command == None) else {"$eq": command};
		typeFilter = {"$ne": None} if (robotType == "all") else {"$eq": robotType};
		idFilter = {"$ne": None} if (robotID == "all") else {"$eq": robotID};
		cursor = self.data.find({"startTime": {"$gte": fromTime, "$lt": toTime},
								 "command": commandFilter,
								 "type": typeFilter,
								 "rewardSignals": {"$ne": []},
								 "_id": idFilter
								 });
		robots = []
		for robot in cursor:
			rsCount = robot["rewardSignals"][0]["count"] + robot["rewardSignals"][1]["count"]
			if rsCount >= minRS:
				robots.append(robot);
		print(len(robots));
		return robots;


	def getUniqueChatters(self, fromTime = datetime(2000, 1, 1, 0, 0, 0, 0) , toTime = datetime.now(), includeMods = False):
		users = []
		if(includeMods):
			cursor = self.chatLog.find({"time": {"$gte": fromTime, "$lt": toTime}});
		else:
			cursor = self.chatLog.find({"time": {"$gte": fromTime, "$lt": toTime}, "user": {"$ne": "janetsbe"}});
		for doc in cursor:
			if(doc["user"] not in users and "http://" not in doc["message"]):
				users.append(doc["user"]);
		return(users);


	def getIssuedCommandCounts(self, robotType, includeNoCommand = False):
		typeFilter = {"$ne": None} if robotType == "all" else {"$eq": robotType};
		commandFilter = {"$ne": "none"} if not includeNoCommand else {"$ne": None};
		cursor = self.data.find({"type": typeFilter, "command": commandFilter});
		commandList = []
		print(cursor.count());
		for doc in cursor:
			try:
				commandList.append(doc["command"])
				#print(doc["command"])
			except:
				print("no such key")
		commandCounts = [{"command": None, "count": None}];
		for element in commandList:
			if(element not in [e["command"] for e in commandCounts]):
				commandCounts.append({"command": element, "count": int(math.ceil(commandList.count(element)/6.0))});
		commandCounts = commandCounts[1:len(commandCounts)];
		commandCounts.sort(key = operator.itemgetter("count"), reverse = True);
		return commandCounts;


	def countRewardSignals(self):
		cursor = self.data.find({"rewardSignals": {"$ne": []}, 
								 "_id": {"$ne": "nextID"},
								 "command": {"$ne": "none"}});
		signalCount = 0;
		signalGivers = [];
		for doc in cursor:
			for user in doc["rewardSignals"][0]["users"]:
				if(len(user) > 0):
					signalGivers.append(user[0]);
			for user in doc["rewardSignals"][1]["users"]:
				if(len(user) > 0):
					signalGivers.append(user[0]);
			signalCount += doc["rewardSignals"][0]["count"];
			signalCount += doc["rewardSignals"][1]["count"];
		print(signalCount)
		return signalGivers;


	def printIssuedCommandInfo(self): 

		simpleCommandCounts = self.getIssuedCommandCounts("simple");
		complexCommandCounts = self.getIssuedCommandCounts("complex");
		simpleIssuedCommandsFile = open("data/simpleIssuedCommands.txt", 'w');
		complexIssuedCommandsFile = open("data/complexIssuedCommands.txt", 'w');

		print("===============================================\nsimple: ");
		print("number different commands: " + str(len(simpleCommandCounts)));
		for entry in simpleCommandCounts:
			simpleIssuedCommandsFile.write(entry["command"] + ":" + str(entry["count"]) + "\n");
		#print(simpleCommandCounts);
		print("\n\nComplex: \n=============================================");
		print("number different commands: " + str(len(complexCommandCounts)));
		#print(complexCommandCounts);

		for entry in complexCommandCounts:
			complexIssuedCommandsFile.write(entry["command"] + ":" + str(entry["count"]) + "\n");
		for entry in simpleCommandCounts:
			simpleIssuedCommandsFile.write(entry["command"] + ":" + str(entry["count"]) + "\n");
		simpleIssuedCommandsFile.close()
		complexIssuedCommandsFile.close()



	def getCommandVotes(self, robotType, fromTime = datetime(2000, 1, 1), toTime = datetime.now()):
		commandVotes = []
		cursor = self.data.find({"type": robotType, "commandVotes": {"$ne": []}, "startTime": {"$gte": fromTime, "$lt": toTime}});
		for doc in cursor:
			commandVotes.append(doc["commandVotes"]);

		voteDict = {}
		for instance in commandVotes:
			for element in instance:
				vote = element["vote"];
				if(vote not in voteDict):
					voteDict[vote] = [];
				for user in element["users"]:
					if user not in voteDict[vote]:
						voteDict[vote].append(user);
		removeKeys = []
		for key in voteDict:
			print(len(voteDict[key]));
			remove = len(voteDict[key]) <= 0;
			if remove:
				removeKeys.append(key);
		for word in removeKeys:
			del(voteDict[word]);
		return voteDict;
			
