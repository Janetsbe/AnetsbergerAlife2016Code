from pymongo import MongoClient;
from datetime import datetime;
from bson.json_util import dumps
import operator;
import subprocess;


#handles writing/reading to/from mongoDB datase and formatting data structures appropriately for 
#storing data while the twitch simulation is running.
class database:

	def __init__(self, databaseName):


		print("initializing DB connections")
		self.client = MongoClient();
		self.db = self.client[databaseName];
		self.data = self.db.robotdata;
		self.messages = self.db.messages;
		self.rawChatLog = self.db.rawChatLog;

		self.initializeCollections();

		self.curRobotCommandVotes = [];
		
		self.curRobotRewardSignals = [{"count": 0, "users": [], "signal": ""}, 
									  {"count": 0, "users": [], "signal": ""}];

		self.prevRobotRewardSignals = [{"count": 0, "users": [], "signal": ""}, 
									  {"count": 0, "users": [], "signal": ""}];


	def setMessage(self, messageType, message, setType = "$set"):
		self.messages.update_one({"_id": messageType}, {setType: {"value": message}});

	def initializeCollections(self):
		messageInits = [
						   {"_id": "command", "value": "none"},
						   {"_id": "controller", "value": [] },
						   {"_id": "robotID", "value": 0},
						   {"_id": "color", "value": "red"},
						   {"_id": "robotType", "value": ""},
						   {"_id": "reward", "value": 0},
						   {"_id": "punish", "value": 0},
						   {"_id": "nextRobot", "value": False},
						   {"_id": "mostCommonCommands", "value": []},
						   {"_id": "mostCommonCommandCounts", "value": []},
						   {"_id": "commandTimeLeft", "value": "60"},
						   {"_id": "instanceTimeLeft", "value": "60"},
						   {"_id": "commandUserQueue", "value": []},
						   {"_id": "rewardUserQueue", "value": []}
				       ];
		for dictionary in messageInits:
			try:
				self.messages.insert_one(dictionary);
			except:
				print(dictionary["_id"] + " already initialized");

		try:
			self.data.insert_one({"_id": "nextID", "value": 0});
		except:
			print("nextID document already exists!");


	def updateField(self, robotID, field, value):
		self.data.update_one({"_id": robotID}, 
							 {"$set": {field: value}});

	def retrieveOneRobot(self, robotID):
		return self.data.find_one({"_id": robotID});

	def addChatMessages(self, messages):
		for message in messages:
			self.rawChatLog.insert_one({
										 "user": message[0],
										 "time": message[1],
										 "message": message[2]
										})
				


	def nextID(self):
		result = self.data.find_one({"_id": "nextID"});
		self.data.update_one({"_id": "nextID"}, {"$inc": {"value": 1}});
		return result["value"];


	def getMostCommonCommand(self):
		mostCommon = "none";
		# print(self.curRobotCommandVotes);
		if(len(self.curRobotCommandVotes) > 0):
			mostCommon = self.curRobotCommandVotes[0]["vote"];
		return mostCommon;


	def clearVoteData(self):
		self.messages.delete_one({"_id": "mostCommonCommands"});
		self.messages.delete_one({"_id": "mostCommonCommandCounts"});
		self.curRobotCommandVotes = [];
		self.initializeCollections();

	def sendMostCommonVotes(self, numVotes):
		votes = [];
		counts = [];
		endPoint = numVotes if (len(self.curRobotCommandVotes) > numVotes) else len(self.curRobotCommandVotes);
		for i in range(0, endPoint):
			votes.append(self.curRobotCommandVotes[i]["vote"]);
			counts.append(self.curRobotCommandVotes[i]["count"]);

		self.setMessage("mostCommonCommands", votes);
		self.setMessage("mostCommonCommandCounts", counts);


	def addRobotInstance(self, ID, body, color, startTime, 
						 controller, command, endTime = None, positions = [], 
						 commandVotes = [], rewardSignals = []):
		robot = { 
					"_id": ID, 
					"type": body, 
					"color": color, 
					"startTime": startTime, 
					"endTime": endTime, 
					"controller": controller, 
					"command": command, 
					"commandVotes": commandVotes,				                 
					"rewardSignals": rewardSignals,
					"positions": positions,
					"rerunPositions": [],
					"sensorData": []
				};
		try:
			self.data.insert_one(robot);
		except:
			print("Cannot insert robot into " + str(database) + "! _id already taken");


	def newControllerRun(self, validRS):
		self.prevRobotRewardSignals = self.curRobotRewardSignals;
		self.curRobotRewardSignals = [{"count": 0, "users": [], "signal": ""}, 
									  {"count": 0, "users": [], "signal": ""}];


	def newCommandRun(self):
		self.curRobotCommandVotes = [];

	
	def endRobot(self, id, endTime):
		print("ending robot");
		self.data.update_one({"_id": str(id)}, {"$set": {"endTime": endTime}});

	def addPreviousRewardSignal(self, id, signal, userName, time):
		index = 1 if signal[1] == "y" else 0;

		self.prevRobotRewardSignals[index]["signal"] = signal;
		self.prevRobotRewardSignals[index]["count"] +=1;
		self.prevRobotRewardSignals[index]["users"].append((userName, time));
		print("Adding to previous RS: " + str(self.prevRobotRewardSignals[index]));

		self.data.update_one(
					{"_id": str(id)},
					{"$set":
						 	{"rewardSignals": self.prevRobotRewardSignals}
					});
		return;

	def addRewardSignal(self, id, signal, userName, time):
		index = 1 if signal[1] == "y" else 0;

		self.curRobotRewardSignals[index]["signal"] = signal;
		self.curRobotRewardSignals[index]["count"] += 1;
		self.curRobotRewardSignals[index]["users"].append((userName, time));
		print("Adding to current RS: " + str(self.curRobotRewardSignals[index]));

		self.data.update_one(
					{"_id":str(id)},
					{"$set":
						 	{"rewardSignals": self.curRobotRewardSignals}
					});
		return;


	def addCommandVote(self, id, commandVote, userName, time):
		print commandVote;
		voteIndex = -1;
		for i in range(0, len(self.curRobotCommandVotes)):

			if(self.curRobotCommandVotes[i]["vote"] == commandVote):

				voteIndex = i;

		if(voteIndex == -1):
			self.curRobotCommandVotes.append({"vote": commandVote,
				 							  "count": 1,
											  "users": [(userName, time)]});

		else:
			self.curRobotCommandVotes[voteIndex]["users"].append((userName, time));
			self.curRobotCommandVotes[voteIndex]["count"] += 1;	
		

		self.curRobotCommandVotes.sort(key = operator.itemgetter("count"), reverse = True);
		self.data.update_one(
					{"_id": str(id)},
					{"$set":
						 	{"commandVotes": self.curRobotCommandVotes}
					});
		self.sendMostCommonVotes(3);



	def backupData(self): 
		subprocess.Popen("backupDB.bat");


	def printCurCommands(self):
		for element in self.curRobotCommandVotes:
			print("vote: " + str(element["vote"]) + "\n" + "count: " + str(element["count"]) + "\n"); 

# database = database();
