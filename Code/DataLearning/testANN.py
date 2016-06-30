from __future__ import division;
import dataReader;
import cma;
import sys;
import random;
import numpy as np;
import os;
import cPickle as pickle;
import matplotlib.pyplot as plt;
import datetime;
import ANN;
import dataHandler;


#tests trained ANNs and records results.


def getSynapses(fileName):

	datFileName = fileName + "-CMA-xrecentbest.dat"
	dataFile = open(datFileName, "r");
	bestFit = 1;
	bestSynapses = [];
	for line in dataFile:
		splitLine = line.split(" ");
		if(splitLine[0] != "%" and float(splitLine[4]) < bestFit):
			bestFit = float(splitLine[4]);
			bestSynapses = np.array([np.tanh(float(value)) for value in splitLine[5::]])
	
	return bestSynapses;




SENSOR_DATA = 0;
REWARD_SIGNALS = 1;
IDS = 2;

###############################################################
#Options - no args yet. to do
robotType = "complex";
command = "jump";
annType = "simplest";
truncated = True;
folder = robotType + "Data/";
nTrials = 1; #number repeat trials on test cases
nSets = 100; #number of testing/training sets (corresponds to number of trained ANNs)
useControlledError = True; #test using controlled error? else uses absolute error

#Lists for results
testDataErrorList = [];
randANNErrorList = [];
shuffledRSErrorList = [];

#Filename formatting based on options.
typeSuffix = robotType + "-";
truncatedSuffix = "-truncated" if truncated else "";
evalFileSuffix = "-evaluated.dat";
randANNEvalFileSuffix = "-randomANNEvaluated.dat"
randRSEvalFileSuffix = "-randomizedRSEvaluated.dat"

synapsesFileSuffix = "-bestSynapses.dat"

errorTypeSuffix = "-controlledError" if useControlledError else ""; 
nTrialsSuffix = "-nTrials(" + str(nTrials) + ")";

dataset = dataHandler.getDataset(command, robotType, 3000);

for i in range(nSets):
	fileName = dataHandler.generateFileName(i);
	wholeFileName = folder +  fileName + truncatedSuffix + errorTypeSuffix + nTrialsSuffix;

	# print(i, wholeFileName);
	if(os.path.exists(wholeFileName + evalFileSuffix) 
	   and os.path.exists(wholeFileName + randRSEvalFileSuffix)
	      and os.path.exists(wholeFileName + randANNEvalFileSuffix)):
		
		testDataErrorList.append(dataHandler.loadPickle(wholeFileName + evalFileSuffix));
		
		shuffledRSErrorList.append(dataHandler.loadPickle(wholeFileName + randRSEvalFileSuffix));

		randANNErrorList.append(dataHandler.loadPickle(wholeFileName + randANNEvalFileSuffix));
	
	else:
		testingIDs = dataHandler.getTestingSetIDs(folder + typeSuffix + fileName);
		testData = dataHandler.getSampledData(dataset, testingIDs, 
											isTraining = False, truncate = True);
		testSynapses = getSynapses(folder + fileName + "-" + annType + truncatedSuffix);
		dataHandler.dumpPickle(testSynapses, fileName + truncatedSuffix + synapsesFileSuffix);

		noIndices = [j for j in range(0, len(testData[REWARD_SIGNALS])) 
										if testData[REWARD_SIGNALS][j] == -1]; # rs | rs = -1
		yesIndices = [p for p in range(0, len(testData[REWARD_SIGNALS])) 
										if testData[REWARD_SIGNALS][p] > -1]; # rs | rs > -1


		# print(len(noIndices), len(yesIndices));
		error = ANN.evaluateSynapses(testSynapses, 
									testData[SENSOR_DATA], testData[REWARD_SIGNALS],
									noIndices, yesIndices, 
									controlledError = useControlledError);
		testDataErrorList.append(error);

		print(i, error);

		dataHandler.dumpPickle(error, wholeFileName + evalFileSuffix);

		shuffledRSTrialResults = [];
		startTime = datetime.datetime.now();
		for k in range(nTrials):
			shuffledRSs = [testData[REWARD_SIGNALS][index] 
						  for index in np.random.permutation(len(testData[REWARD_SIGNALS]))];

			noIndicesShuffled = [a for a in range(0, len(testData[REWARD_SIGNALS]))
											if shuffledRSs[a] == -1]; # rs | rs = -1
			yesIndicesShuffled = [b for b in range(0, len(testData[REWARD_SIGNALS]))
											if shuffledRSs[b] > -1]; # rs | rs > -1
			# print(testData[SENSOR_DATA][0], testSynapses);
			shuffledRSTrialResults.append(ANN.evaluateSynapses(testSynapses,
														testData[SENSOR_DATA],
														shuffledRSs, noIndicesShuffled,
														yesIndicesShuffled, controlledError = useControlledError));
		shuffledRSErrorList.append(shuffledRSTrialResults);
		dataHandler.dumpPickle(shuffledRSTrialResults, wholeFileName + randRSEvalFileSuffix);
		# print("time taken", datetime.datetime.now() - startTime);
		print(np.mean(shuffledRSTrialResults));


		randomANNTrialResults = [];
		startTime = datetime.datetime.now();
		for l in range(nTrials):
			randomANN = ANN.getSimplestANNWeights(robotType = robotType);
			randomANNTrialResults.append(ANN.evaluateSynapses(randomANN, testData[SENSOR_DATA], 
														testData[REWARD_SIGNALS], noIndices,
														yesIndices, controlledError = useControlledError));
		# print("time taken", datetime.datetime.now() - startTime);

		randANNErrorList.append(randomANNTrialResults);
		dataHandler.dumpPickle(randomANNTrialResults, wholeFileName + randANNEvalFileSuffix);

		print(np.mean(randomANNTrialResults));



# print(testDataErrorList);
# print(np.mean(testDataErrorList));
# print(np.std(testDataErrorList));

# print(shuffledRSErrorList);
# print(np.mean(shuffledRSErrorList));
# print(np.std(shuffledRSErrorList));

# scipy.stats.stats.ttest_ind(testDataErrorList, shuffledRSErrorList);

# evolvedANNError = evaluateSynapses(testSynapses, testData[SENSOR_DATA], testData[REWARD_SIGNALS], noIndices, yesIndices);


