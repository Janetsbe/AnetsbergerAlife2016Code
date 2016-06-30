import numpy as np;
from scipy.stats.stats import pearsonr;
from scipy.stats.stats import spearmanr;
from scipy.stats.stats import linregress;
import matplotlib.pyplot as plt;
import dataReader as read;
import time;

#Written to do a few informal looks at the data. Checks for correlation between feature of touch sensor data and reinforcements.

reader = read.dataReader("rerunDB")


robotType = "simple"
command = "jump"

dataset = reader.retrieveSensorData(robotType = robotType, command = command, minTimesteps = 3000);

SENSOR_DATA = 0;
REWARD_SIGNALS = 1;

print(dataset[1].count(-1));
print(dataset[1].count(1));

meanGroundedTime = []
for robot in dataset[0]:
	robotGroundedTimesteps = []
	for row in robot:
		rowGrounded = 1 if 1 in row else 0;
		robotGroundedTimesteps.append(rowGrounded);
	meanGroundedTime.append(np.mean(robotGroundedTimesteps));

print(np.mean(meanGroundedTime), np.std(meanGroundedTime), min(meanGroundedTime), max(meanGroundedTime));

rp = pearsonr(meanGroundedTime, dataset[REWARD_SIGNALS]);
print(rp);
rs = spearmanr(meanGroundedTime, dataset[REWARD_SIGNALS]);
print(rs);
lr = linregress(meanGroundedTime, dataset[REWARD_SIGNALS]);
print(lr);

fit = np.polyfit(meanGroundedTime, dataset[REWARD_SIGNALS], 1);

print(fit);
fitfn = np.poly1d(lr[0:2]);

plt.plot(meanGroundedTime, dataset[REWARD_SIGNALS], 'go', np.arange(.4, 1.1, .01), fitfn(np.arange(.4, 1.1, .01)), '--k');

plt.title("Proportion Time Grounded and Normalized Reinforcement Signal" 
		+ "\n For " + robotType[0].upper() + robotType[1:] + " Robot with \"jump\" Command");
plt.ylabel("Normalized Reinforcement Signal");
plt.xlabel("Proportion of Time Grounded");
plt.axis([.45, 1.05, -1.1, 1.1]);
plt.show();

################################################
# Slightly different feature
################################################

meanSensorValues = [np.mean(sensorValues) for sensorValues in dataset[SENSOR_DATA]]

rp = pearsonr(meanSensorValues, dataset[REWARD_SIGNALS]);
print(rp);
rs = spearmanr(meanSensorValues, dataset[REWARD_SIGNALS]);
print(rs);

fit = np.polyfit(meanSensorValues, dataset[REWARD_SIGNALS], 1);
fitfn = np.poly1d(fit);

plt.plot(meanSensorValues, dataset[REWARD_SIGNALS], 'go', np.arange(.2, .65, .025), fitfn(np.arange(.2, .65, .025)), '--k');

plt.title("Mean Sensor Value and Normalized Reinforcement Signal "
				+ "\n For " + robotType[0].upper() + robotType[1:] + " Robot with \"jump\" Command");
plt.ylabel("Normalized Reinforcement Signal");
plt.xlabel("Mean Touch Sensor Value");

plt.show();
