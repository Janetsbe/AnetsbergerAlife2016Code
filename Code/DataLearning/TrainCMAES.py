from __future__ import division;
import dataReader;
import dataHandler
import cma;
import sys;
import random;
import numpy as np;
import os;
import cPickle as pickle;
import matplotlib.pyplot as plt;
import datetime;
import ANN;



def trainSimplestANNCMA(synapses, inputs, RSs, noIndices, yesIndices):
	synapsesReshaped = ANN.getSimplestANNWeights(synapses, robotType = "complex");

	return ANN.evaluateSynapses(synapsesReshaped, inputs, RSs, noIndices, yesIndices);

SENSOR_DATA = 0;
REWARD_SIGNALS = 1;
IDS = 2;

#Setting variables - no args yet. to do.
robotType = "complex"
truncate = True;
folder = robotType + "Data/"
truncateSuffix = "-truncated" if truncate else "";
annType = 'simplest';


numRuns = 1; #number of ANNs to train - sequentially. Each draws from a different training set. 


for i in range(numRuns):
	
	dataset = dataHandler.getDataset("jump", robotType, 1000);
	setNumber = dataHandler.nextSetNumber();
	print("setNumber", setNumber);
	fileName = dataHandler.generateFileName(setNumber);
	trainingIDs = dataHandler.getTrainingSetIDs(robotType + "-" + fileName, dataset[IDS]);
	trainData = dataHandler.getSampledData(dataset, trainingIDs, truncate = truncate);
	print("|train set|", len(trainData[IDS]))

	del dataset; #free up dataset ~300mb!

	#used in calculating controlled error
	noIndices = [i for i in range(0, len(trainData[REWARD_SIGNALS])) if trainData[REWARD_SIGNALS][i] == -1]; # rs | rs = -1
	yesIndices = [i for i in range(0, len(trainData[REWARD_SIGNALS])) if trainData[REWARD_SIGNALS][i] != -1]; # rs | rs < 1


	#Set CMAES options;
	opts = cma.CMAOptions()
	opts.set("verb_disp", 1);
	opts.set("verb_filenameprefix", folder + fileName + "-" + annType + truncateSuffix + "-CMA-");

	if(annType == "simplest"):
		initialGuess = ANN.getSimplestANNWeights(robotType = robotType);
		res = cma.fmin(trainSimplestANNCMA, initialGuess, .1, args = (trainData[SENSOR_DATA], 
								trainData[REWARD_SIGNALS], noIndices, yesIndices), options = opts);
	
	#unused branch for future development using multiple different neural networks.
	elif(annType == "CTRNN"):
		print("not there yet - exiting");
		exit();

	print(res);





