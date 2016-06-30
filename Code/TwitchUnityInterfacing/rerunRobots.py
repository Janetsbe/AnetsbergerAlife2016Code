import database;
import DBreader;
import sys;
import time;
from datetime import datetime;

def hasSensorData(robot):
	hasSensorData = False;
	try: 
		sensorData = robot["sensorData"];
		hasSensorData = True if sensorData != [] else False;
	except KeyError:
		print("no sensordata recorded yet");
		hasSensorData = False;

	return hasSensorData;


print(len(sys.argv));
robotID = "all" if len(sys.argv) == 1 else str(sys.argv[1]);
command = "jump";
robotType = "complex"
minimumRS = "1";
print(robotID);
time.sleep(2);

reader = DBreader.DBreader();
db = database.database("rerunDB");

robots = reader.getRobotData(command = command, robotType = robotType, robotID = robotID);
print(len(robots));
for robot in robots:
	startTime = robot["startTime"]
	endTime = robot["endTime"]
	runTime = endTime - startTime;
	print(runTime);
	robotStart = datetime.now();
	runRobot = True;
	#deep copy robot into rerun database.
	db.addRobotInstance(robot["_id"], 
						robot["type"], 
						robot["color"], 
						robot["startTime"], 
						robot["controller"], 
						robot["command"],
						endTime = robot["endTime"],
						positions = robot["positions"],
						commandVotes = robot["commandVotes"],
						rewardSignals = robot["rewardSignals"]);
	db.setMessage("color", robot["color"]);
	db.setMessage("controller", robot["controller"]);
	db.setMessage("command", robot["command"]);
	db.setMessage("robotType", robot["type"]);
	db.setMessage("robotID", robot["_id"]);
	
	db.updateField(robot["_id"], "rerunPositions", []);
	curRobot = db.retrieveOneRobot(robot["_id"]);
	db.setMessage("nextRobot", False);
	if(not(hasSensorData(curRobot))):    
		print("running robot #" + robot["_id"]);
		db.setMessage("nextRobot", True);
		while(runRobot):
			if((datetime.now() - robotStart) >= runTime):
				print("Ending robot");
				db.setMessage("nextRobot", True);
				runRobot = False;
	else:
		print("robot #" + robot["_id"] + " already has sensor data!");