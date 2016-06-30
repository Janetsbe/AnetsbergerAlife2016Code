from pymongo import MongoClient;
from datetime import datetime;
from datetime import date;
from bson.json_util import dumps;
import numpy as np
import math;
import operator;
import subprocess;
import dataHandler;

#Gets data for training predictive model from.

class dataReader:

	def __init__(self, dbName):
		self.client = MongoClient();
		self.db = self.client[dbName];
		self.data = self.db.robotdata;
		self.chatLog = self.db.rawChatLog;

	def retrieveSensorData(self, robotType = "all", minTimesteps = 0, 
					  command = "all", minRS = 1, robotID = "all", 
					  fromTime = datetime(2000, 1, 1), toTime = datetime.now()):

		commandFilter = {"$ne": None} if (command == "all") else {"$eq": command};
		typeFilter = {"$ne": None} if (robotType == "all") else {"$eq": robotType};
		idFilter = {"$ne": None} if (robotID == "all") else {"$eq": robotID};
		cursor = self.data.find({"startTime": {"$gte": fromTime, "$lt": toTime},
								 "command": commandFilter,
								 "type": typeFilter,
								 "rewardSignals": {"$ne": []},
								 "_id": idFilter
								 });

		print("cursor length", cursor.count());
		dataset = [[], [], []]

		sensorLength = 3 if robotType == "simple" else 7;

		for robot in cursor:
			rsCount = robot["rewardSignals"][0]["count"] + robot["rewardSignals"][1]["count"]
			if(rsCount >= minRS and len(robot["sensorData"]) > minTimesteps 
								and len(robot["sensorData"][0]) == 3):

				sensorData = robot["sensorData"];
				noCount = robot["rewardSignals"][0]["count"];
				yesCount = robot["rewardSignals"][1]["count"];
	
				normalizedRSValue = (yesCount - noCount)/float(rsCount);
				rID = robot["_id"];
				dataset[0].append(sensorData);
				dataset[1].append(normalizedRSValue)
				dataset[2].append(rID)
		
		return dataset;

