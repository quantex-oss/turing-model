import numpy as np

from turing_models.models.gbm_process import getPathsAssets, getPathsAssets_new

numAssets = 3
numPaths = 10
numTimeSteps = 10
t = 0.8
mus = np.array([0.1, 0.2, 0.3])
stockPrices = np.array([1.0, 2.0, 3.0])
volatilities = np.array([0.1, 0.2, 0.3])
corrMatrix = np.array([0.1, 0.2, 0.3, 0.1, 0.2, 0.3, 0.1, 0.2, 0.3]).reshape((3, 3))
seed = 1234

data1 = getPathsAssets(numAssets,
                      numPaths,
                      numTimeSteps,
                      t,
                      mus,
                      stockPrices,
                      volatilities,
                      corrMatrix,
                      seed)
# print(data.shape)
data2 = getPathsAssets_new(numAssets,
                      numPaths,
                      numTimeSteps,
                      t,
                      mus,
                      stockPrices,
                      volatilities,
                      corrMatrix,
                      seed)
print(data1 == data2)