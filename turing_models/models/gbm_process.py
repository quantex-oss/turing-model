import numpy as np
from numba import njit, float64, int64

from turing_models.utilities.mathematics import cholesky

###############################################################################

@njit(float64[:, :](int64, int64, float64, float64, float64, float64, int64),
      cache=True, fastmath=True)
def getPaths(numPaths,
             numTimeSteps,
             t,
             mu,
             stockPrice,
             volatility,
             seed):
    ''' Get the simulated GBM process for a single asset with many paths and
    time steps. Inputs include the number of time steps, paths, the drift mu,
    stock price, volatility and a seed. '''

    np.random.seed(seed)
    dt = t / numTimeSteps
    vsqrtdt = volatility * np.sqrt(dt)
    m = np.exp((mu - volatility * volatility / 2.0) * dt)
    Sall = np.empty((2 * numPaths, numTimeSteps + 1))

    # This should be less memory intensive as we only generate randoms per step
    Sall[:, 0] = stockPrice
    for it in range(1, numTimeSteps + 1):
        g1D = np.random.standard_normal((numPaths))
        for ip in range(0, numPaths):
            w = np.exp(g1D[ip] * vsqrtdt)
            Sall[ip, it] = Sall[ip, it - 1] * m * w
            Sall[ip + numPaths, it] = Sall[ip + numPaths, it - 1] * m / w

    return Sall


def GBMsimulator(numAssets,
                 numPaths,
                 numTimeSteps,
                 t,
                 mus,
                 stockPrices,
                 volatilities,
                 corrMatrix,
                 seed):

    np.random.seed(seed)
    dt = t / numTimeSteps
    c = np.linalg.cholesky(corrMatrix)
    S = np.zeros([2 * numPaths, numAssets, numTimeSteps+1])
    for ip in range(0, numPaths):
        S[ip, :, 0] = stockPrices
        S[ip + numPaths, :, 0] = stockPrices
        for i in range(1, numTimeSteps+1):
            drift = (mus - 0.5 * volatilities ** 2) * dt
            Z = np.random.standard_normal((numAssets))
            diffusion = np.matmul(c, Z) * np.sqrt(dt)
            S[ip, :, i] = S[ip, :, i-1] * np.exp(drift + diffusion)
            S[ip + numPaths, :, i] = S[ip + numPaths, :, i-1] * np.exp(drift + diffusion)
    return S
###############################################################################


# @njit(float64[:, :, :](int64, int64, int64, float64, float64[:], float64[:],
#                        float64[:], float64[:, :], int64),
#       cache=True, fastmath=True)
@njit
def getPathsAssets(numAssets,
                   numPaths,
                   numTimeSteps,
                   t,
                   mus,
                   stockPrices,
                   volatilities,
                   corrMatrix,
                   seed):
    ''' Get the simulated GBM process for a number of assets and paths and num
    time steps. Inputs include the number of assets, paths, the vector of mus,
    stock prices, volatilities, a correlation matrix and a seed. '''

    np.random.seed(seed)
    dt = t / numTimeSteps
    vsqrtdts = volatilities * np.sqrt(dt)
    m = np.exp((mus - volatilities * volatilities / 2.0) * dt)

    Sall = np.empty((2 * numPaths, numTimeSteps + 1, numAssets))

    g = np.random.standard_normal((numPaths, numTimeSteps + 1, numAssets))
    c = cholesky(corrMatrix)
    gCorr = np.empty((numPaths, numTimeSteps + 1, numAssets))

    # Calculate the dot product
    for ip in range(0, numPaths):
        for it in range(0, numTimeSteps+1):
            for ia in range(0, numAssets):
                gCorr[ip][it][ia] = 0.0
                for ib in range(0, numAssets):
                    gCorr[ip][it][ia] += g[ip][it][ib] * c[ia][ib]

    for ip in range(0, numPaths):
        for ia in range(0, numAssets):
            Sall[ip, 0, ia] = stockPrices[ia]
            Sall[ip + numPaths, 0, ia] = stockPrices[ia]

    for ip in range(0, numPaths):
        for it in range(1, numTimeSteps + 1):
            for ia in range(0, numAssets):
                z = gCorr[ip, it, ia]
                w = np.exp(z * vsqrtdts[ia])
                v = m[ia]
                Sall[ip, it, ia] = Sall[ip, it - 1, ia] * v*w
                Sall[ip + numPaths, it, ia] = Sall[ip + numPaths,
                                                   it - 1, ia] * v/w

    return Sall


@njit(float64[:, :, :](int64, int64, int64, float64, float64[:], float64[:],
                       float64[:], float64[:, :], int64),
      cache=True, fastmath=True)
def getPathsAssets_new(numAssets,
                   numPaths,
                   numTimeSteps,
                   t,
                   mus,
                   stockPrices,
                   volatilities,
                   corrMatrix,
                   seed):
    ''' Get the simulated GBM process for a number of assets and paths and num
    time steps. Inputs include the number of assets, paths, the vector of mus,
    stock prices, volatilities, a correlation matrix and a seed. '''

    np.random.seed(seed)
    dt = t / numTimeSteps
    vsqrtdts = volatilities * np.sqrt(dt)
    m = np.exp((mus - volatilities * volatilities / 2.0) * dt)

    Sall = np.empty((2 * numPaths, numTimeSteps + 1, numAssets))

    g = np.random.standard_normal((numPaths, numTimeSteps + 1, numAssets))
    c = cholesky(corrMatrix)
    gCorr = np.zeros((numPaths, numTimeSteps + 1, numAssets))

    # Calculate the dot product
    for ip in range(0, numPaths):
        Sall[ip, 0, :] = stockPrices
        Sall[ip + numPaths, 0, :] = stockPrices
        for it in range(0, numTimeSteps+1):
            for ia in range(0, numAssets):
                # gCorr[ip][it][ia] = 0.0
                # for ib in range(0, numAssets):
                #     gCorr[ip][it][ia] += g[ip][it][ib] * c[ia][ib]
                gCorr[ip][it][ia] += np.sum(np.multiply(g[ip][it][:], c[ia][:]))
                if it > 0:
                    z = gCorr[ip, it, ia]
                    w = np.exp(z * vsqrtdts[ia])
                    v = m[ia]
                    Sall[ip, it, ia] = Sall[ip, it - 1, ia] * v*w
                    Sall[ip + numPaths, it, ia] = Sall[ip + numPaths,
                                                       it - 1, ia] * v/w
    return Sall
###############################################################################


#@njit(float64[:, :](int64, int64, float64, float64[:], float64[:], float64[:],
#                   float64[:, :], int64),
#                   cache=True, fastmath=True)
@njit
def getAssets(numAssets,
              numPaths,
              t,
              mus,
              stockPrices,
              volatilities,
              corrMatrix,
              seed):

    ''' Get the simulated GBM process for a number of assets and paths for one
    time step. Inputs include the number of assets, paths, the vector of mus,
    stock prices, volatilities, a correlation matrix and a seed. '''

    np.random.seed(seed)
    vsqrtdts = volatilities * np.sqrt(t)
    m = np.exp((mus - volatilities * volatilities / 2.0) * t)
    Sall = np.empty((2 * numPaths, numAssets))
    g = np.random.standard_normal((numPaths, numAssets))
    c = cholesky(corrMatrix)
    gCorr = np.empty((numPaths, numAssets))

    # Calculate the dot product
    for ip in range(0, numPaths):
        for ia in range(0, numAssets):
            gCorr[ip][ia] = 0.0
            for ib in range(0, numAssets):
                gCorr[ip][ia] += g[ip][ib] * c[ia][ib]

    for ip in range(0, numPaths):
        for ia in range(0, numAssets):
            z = gCorr[ip, ia]
            w = np.exp(z * vsqrtdts[ia])
            Sall[ip, ia] = stockPrices[ia] * m[ia] * w
            Sall[ip + numPaths, ia] = stockPrices[ia] * m[ia] / w

    return Sall

###############################################################################


class TuringGBMProcess():

    def getPaths(self,
                 numPaths: int,
                 numTimeSteps: int,
                 t: float,
                 mu: float,
                 stockPrice: float,
                 volatility: float,
                 seed: int):
        ''' Get a matrix of simulated GBM asset values by path and time step.
        Inputs are the number of paths and time steps, the time horizon and
        the initial asset value, volatility and random number seed. '''

        paths = getPaths(numPaths, numTimeSteps,
                         t, mu, stockPrice, volatility, seed)

        return paths

###############################################################################

    def getPathsAssets(self,
                       numAssets,
                       numPaths,
                       numTimeSteps,
                       t,
                       mus,
                       stockPrices,
                       volatilities,
                       corrMatrix,
                       seed):
        ''' Get a matrix of simulated GBM asset values by asset, path and time
        step. Inputs are the number of assets, paths and time steps, the time-
        horizon and the initial asset values, volatilities and betas. '''

        if numTimeSteps == 2:
            paths = getAssets(numAssets, numPaths,
                              t, mus, stockPrices,
                              volatilities, corrMatrix, seed)
        else:
            paths = getPathsAssets(numAssets, numPaths, numTimeSteps,
                                   t, mus, stockPrices,
                                   volatilities, corrMatrix, seed)
        return paths

###############################################################################
