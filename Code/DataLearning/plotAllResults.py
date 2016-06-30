#Code modified from matplotlib.org at http://www.matplotlib.org/examples/api/barchart_demo.html

#Tests results of trained ANN test.

import numpy as np
import matplotlib.pyplot as plt
import pickle;
from scipy.stats.stats import ttest_ind;



#set number to begin from.
startSetNo = 0;
#number of sets to use
N = 100;

#No options - hardcoded filenames. Clean up to do.
setNumbers = [i for i in range(startSetNo, N)]

controlledErrorSuffix = "-controlledError";
truncatedSuffix = "-truncated";
nTrialsSuffix = "-nTrials(1)";
wholeSuffix=  truncatedSuffix + controlledErrorSuffix + nTrialsSuffix;
# trainEvalData = [pickle.load(open(folder + "trainingSetIDs " + str(i) + "truncated-trainSetEvaluated.dat")) for i in setNumbers)];
simpleTestSampleData = [pickle.load(open("simpleData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-evaluated.dat")) for i in setNumbers];
simpleShuffledData = [pickle.load(open("simpleData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-randomizedRSEvaluated.dat")) for i in setNumbers];
simpleRandomANNData = [pickle.load(open("simpleData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-randomANNEvaluated.dat")) for i in setNumbers];

complexTestSampleData = [pickle.load(open("complexData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-evaluated.dat")) for i in setNumbers];
complexShuffledData = [pickle.load(open("complexData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-randomizedRSEvaluated.dat")) for i in setNumbers];
complexRandomANNData = [pickle.load(open("complexData/" + "trainingSetIDs " + str(i) + wholeSuffix + "-randomANNEvaluated.dat")) for i in setNumbers];


ind = np.arange(N);  # the x locations for the groups
width = 0.2;       # the width of the bars

print("Ttest simple Exp. vs Permuted", ttest_ind(simpleTestSampleData, simpleShuffledData));
print("Ttest simple Exp. vs Random", ttest_ind(simpleTestSampleData, simpleRandomANNData));


print("Ttest complex Exp. vs Permuted", ttest_ind(complexTestSampleData, complexShuffledData));
print("Ttest complex Exp. vs Random", ttest_ind(complexTestSampleData, complexRandomANNData));


fig, ax = plt.subplots();

x = [.15, .25, .35, .55, .65, .75]
point0 = ax.errorbar(x[2], np.mean(simpleTestSampleData),
			yerr = np.std(simpleTestSampleData), 
			fmt = 'o', markersize = 5, color = 'g', ecolor = 'g');
point1 = ax.errorbar(x[1], np.mean(simpleShuffledData),
			yerr = np.std(simpleShuffledData), 
			fmt = 'o', markersize = 5, color = 'r', ecolor = 'r');
point2 = ax.errorbar(x[0], np.mean(simpleRandomANNData),
			yerr = np.std(simpleRandomANNData), 
			fmt = 'o', markersize = 5, color = 'b', ecolor = 'b');
point3 = ax.errorbar(x[5], np.mean(simpleTestSampleData),
			yerr = np.std(complexTestSampleData), 
			fmt = 'o', markersize = 5, color = 'g', ecolor = 'g');
point4 = ax.errorbar(x[4], np.mean(simpleShuffledData),
			yerr = np.std(complexShuffledData), 
			fmt = 'o', markersize = 5, color = 'r', ecolor = 'r');
point5 = ax.errorbar(x[3], np.mean(simpleRandomANNData),
			yerr = np.std(complexRandomANNData), 
			fmt = 'o', markersize = 5, color = 'b', ecolor = 'b');
ax.set_ylabel("Error");
ax.set_xticks(x)
ax.set_xticklabels(["", "Simple Robot", "", "", "Complex Robot", ""]);
ax.set_title("Mean Error of Predictive Model Across\n 100 Trials for Simple"
	            + " and Complex Robots");
ax.legend((point0[0], point1[0], point2[0]), ("Experiment", "Permuted\nControl", "Random\nControl"),
		loc = 9,  numpoints = 1, fontsize = 10);
plt.xlim((x[0] - .1, x[len(x) -1] + .1));
plt.ylim((.395, .53))

plt.show();