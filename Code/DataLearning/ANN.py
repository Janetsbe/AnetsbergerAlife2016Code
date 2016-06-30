import numpy as np;
import matplotlib.pyplot as plt;
import time;
import datetime;

#ANN methods used for "Robots can ground crowd proposed symbols by forming theory of group mind"
#Author: Joey Anetsberger

#For the "simplest" ANN consisting of four neurons. Three/seven input neurons all connected to one output
#and output neuron self-recurrent connection.
def getSimplestANNWeights(synapses = [], robotType = "simple"):
	weights = []
	nSynapses = 4 if robotType == "simple" else 8;
	if len(synapses) == 0:
		weights = (2 * (np.random.random(nSynapses) - .5));
	else:
		weights = np.array([np.tanh(synapse) for synapse in synapses[0:nSynapses]]);

	return weights;

#For the "simplest" ANN consisting of four neurons. Three/seven input neurons all connected to one output
#and output neuron self-recurrent connection.
def runSimplestANN(inputs, synapses):
	
	for i in range(len(inputs) - 1):
		inputs[i + 1][len(inputs[i]) -1] = np.tanh(np.dot(inputs[i], synapses));
	output =  np.tanh(np.dot(inputs[len(inputs) - 1], synapses))

	return output;


#Fitness evaluation. "controlled error" weights two sets equally: 
#those which received all "no" and those which received at least one "yes"
#otherwise error is calculated by difference of all O and O' (RSs[i] and outs[i])
def evaluateSynapses(synapses, sensorData, RSs, noIndices, yesIndices, ANNType = "simplest", controlledError = True):

	outs = [0] * len(RSs);

	for j in range(0, len(sensorData)):
		if(ANNType == "simplest"):
			output = runSimplestANN(sensorData[j], synapses);
			outs[j] = output;

	#print("mean output: ", np.mean(outs), "std dev.:", np.std(outs), "range: ", min(outs), max(outs));
	wy = 1;
	wn = 1;

	if(controlledError):
		error = ( wn * ( sum([abs(RSs[i] - outs[i])/2 for i in noIndices])/len(noIndices) )  
				+ wy * ( sum([abs(RSs[i] - outs[i])/2 for i in yesIndices])/len(yesIndices) ) ) / (wy + wn)
	else:
		error =  sum([abs(RSs[i] - outs[i])/2 for i in range(len(RSs))])/len(RSs);
				

	return error;
