from __future__ import division;
import dataReader;
import sys;
import random;
import numpy as np;
import os;
import cPickle as pickle;
import matplotlib.pyplot as plt;
import datetime;
import ANN;


#get a sample of a dataset for training, or the testing set to test against a specific training set.
#also modifies sensor data to be an array of neurons for use in an ANN;
def getSampledData(dataset, sampleIDs, isTraining = True, annType = "simplest", truncate = False):
	SENSOR_DATA = 0;
	REWARD_SIGNALS = 1;
	IDS = 2;

	# print("num of IDs", len(dataset[IDS]))
	nAdded = 0;
	data = [[], [], []];
	for i in range(len(dataset[IDS])):
		addThisID = False;
		if(dataset[IDS][i] in sampleIDs and isTraining):
			# print("adding training ID to set: " + str(dataset[IDS][i]));
			addThisID = True;
		elif(not(dataset[IDS][i] in sampleIDs) and not(isTraining)):
			# print("adding test ID to set: " + str(dataset[IDS][i]));
			addThisID = True;
		if(addThisID):
			data[SENSOR_DATA].append([]);
			dataLength = min([len(sensorData) for sensorData in dataset[SENSOR_DATA]]) if truncate else len(dataset[SENSOR_DATA][i]);
			for j in range(dataLength):

				#convert sensor data to np.array for speed list was 2x slower).
				#add a 4th value to represent output neuron. "Sensor data" effectively becomes neurons
				data[SENSOR_DATA][nAdded].append(np.array(dataset[SENSOR_DATA][i][j] + [0.0])); 

			# trainData[SENSOR_DATA].append(dataset[SENSOR_DATA][i]);
			data[REWARD_SIGNALS].append(dataset[REWARD_SIGNALS][i]);
			data[IDS].append(dataset[IDS][i]);
			nAdded += 1;
	return data;


def getDataset(command, robotType, minTimesteps):
	reader = dataReader.dataReader("rerunDB");
	dataset = reader.retrieveSensorData(command = command, 
							robotType = robotType, minTimesteps = minTimesteps);
	return dataset;

def generateFileName(setNumber):
	trainingIDsFileName = "trainingSetIDs " + str(setNumber);
	return trainingIDsFileName;


def loadPickle(fileName):
	try:
		f = open(fileName, 'r');
		data = pickle.load(f);
		f.close();	
	except:
		print("CANNOT LOAD PICKLE EXCEPTION In loadPickle(). \n" 
		       + "Does file: \"" + fileName + "\" exist? \n Exiting.");
		exit();
	return data;

def dumpPickle(data, fileName):
	f = open(fileName, 'w');
	pickle.dump(data, f);
	f.close();



#if there is a training data set under the current set number's file name, retrieve that.
#otherwise, generate a set and save it.
def getTrainingSetIDs(fileName, IDs):
	datFileName = fileName + ".dat";
	if(os.path.exists(datFileName)):	
		IDSet = loadPickle(datFileName);
	else:
		IDSet = [IDs[index] for index 
				in (np.random.permutation(range(len(IDs)))[0:len(IDs)//2])];
		dumpPickle(IDSet, datFileName);
	return IDSet;

def getTestingSetIDs(fileName):
	# print("Filename", fileName);
	datFileName = fileName + ".dat";
	if(os.path.exists(datFileName)):
		IDSet = loadPickle(datFileName);
	else:
		print("No such ID set exists. " + fileName + " Exiting.");
		exit();
	return IDSet;


def nextSetNumber():
	if(os.path.exists("currentSetNumber.dat")):	
		setFile = open("currentSetNumber.dat", 'r');
		setNumber = int(pickle.load(setFile));
		setFile.close();
		setFile = open("currentSetNumber.dat", 'w');
		nextSet = setNumber + 1;
		pickle.dump(nextSet, setFile);
		setFile.close();
	else:
		print("NO CURRENT SET NUMBER INITIALIZED - EXITING");
		exit();
	return setNumber;


# noIndices = [i for i in range(0, len(trainData[REWARD_SIGNALS])) if trainData[REWARD_SIGNALS][i] == -1]; # rs | rs = -1
# yesIndices = [i for i in range(0, len(trainData[REWARD_SIGNALS])) if trainData[REWARD_SIGNALS][i] != -1]; # rs | rs < 1
