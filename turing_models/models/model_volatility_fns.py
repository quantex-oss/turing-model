import numpy as np
import math
from numba import njit, float64
from scipy.interpolate import CubicSpline

from turing_models.utilities.mathematics import N
from turing_models.utilities.error import TuringError

###############################################################################
# Parametric functions for option volatility to use in a Black-Scholes model
###############################################################################

from enum import Enum


class TuringVolFunctionTypes(Enum):
    CLARK = 0
    SABR = 1
    SABR_BETA_ONE = 2
    SABR_BETA_HALF = 3
    BBG = 4
    CLARK5 = 5
    SVI = 6
    SSVI = 7
    VANNA_VOLGA = 8


###############################################################################


@njit(float64(float64[:], float64, float64, float64),
      fastmath=True, cache=True)
def volFunctionClark(params, f, k, t):
    ''' Volatility Function in book by Iain Clark generalised to allow for
    higher than quadratic power. Care needs to be taken to avoid overfitting.
    The exact reference is Clark Page 59. '''

    if f < 0.0:
        print("f:", f)
        raise TuringError("Forward is negative")

    if k < 0.0:
        print("k:", k)
        raise TuringError("Strike is negative")

    x = np.log(f/k)
    sigma0 = np.exp(params[0])
    arg = x / (sigma0 * np.sqrt(t))
    deltax = N(arg) - 0.50  # The -0.50 seems to be missing in book
    f = 0.0
    for i in range(0, len(params)):
        f += params[i] * (deltax ** i)

    return np.exp(f)

###############################################################################


@njit(float64(float64[:], float64, float64, float64),
      fastmath=True, cache=True)
def volFunctionBloomberg(params, f, k, t):
    ''' Volatility Function similar to the one used by Bloomberg. It is
    a quadratic function in the spot delta of the option. It can therefore
    go negative so it requires a good initial guess when performing the
    fitting to avoid this happening. The first parameter is the quadratic
    coefficient i.e. sigma(K) = a * D * D + b * D + c where a = params[0],
    b = params[1], c = params[2] and D is the spot delta.'''

    numParams = len(params)

    # Rather than pass in the ATM vol, I imply it from the delta=0.50 curve
    sigma = 0.0
    for i in range(0, len(params)):
        pwr = numParams - i - 1
        sigma += params[i] * ((0.50) ** pwr)

    vsqrtt = sigma * np.sqrt(t)

    d1 = np.log(f/k) / vsqrtt + vsqrtt/2.0
    delta = N(d1)

    v = 0.0
    for i in range(0, len(params)):
        pwr = numParams - i - 1
        v += params[i] * (delta ** pwr)

    return v

###############################################################################
# I do not jit this so it can be called from a notebook with a vector of strike
# Also, if I vectorise it it fails as it cannot handle a numpy array as input
###############################################################################


@njit(float64(float64[:], float64, float64, float64),
      fastmath=True, cache=True)
def volFunctionSVI(params, f, k, t):
    ''' Volatility Function proposed by Gatheral in 2004. Increasing a results
    in a vertical translation of the smile in the positive direction.
    Increasing b decreases the angle between the put and call wing, i.e.
    tightens the smile. Increasing rho results in a counter-clockwise rotation
    of the smile. Increasing m results in a horizontal translation of the smile
    in the positive direction. Increasing sigma reduces the at-the-money
    curvature of the smile. '''

    x = np.log(f/k)

    a = params[0]
    b = params[1]
    rho = params[2]
    m = params[3]
    sigma = params[4]

    vart = a + b*(rho*(x-m)+np.sqrt((x-m)**2 + sigma*sigma))
    v = np.sqrt(vart/t)
    return v

###############################################################################
###############################################################################
# Gatheral SSVI surface SVI and equivalent local volatility
# Code from https://wwwf.imperial.ac.uk/~ajacquie/IC_AMDP/IC_AMDP_Docs/Code/SSVI.pdf
###############################################################################
###############################################################################


@njit(float64(float64, float64), fastmath=True, cache=True)
def phiSSVI(theta, gamma):
    phi = (1.0/gamma/theta) * (1.0 - (1.0 - np.exp(-gamma*theta))/gamma/theta)
    return phi


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def SSVI(x, gamma, sigma, rho, t):
    ''' This is the total variance w = sigma(t) x sigma(t) (0,t) x t '''

    theta = sigma * sigma * t
    p = phiSSVI(theta, gamma)
    px = p * x
    g = px + rho
    v = 0.5 * theta * (1. + rho * px + np.sqrt(g**2 + 1. - rho * rho))
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def SSVI1(x, gamma, sigma, rho, t):
    # First derivative with respect to x
    theta = sigma * sigma * t
    p = phiSSVI(theta, gamma)
    px = p * x
    v = 0.5 * theta * p * \
        (px + rho * np.sqrt(px**2 + 2. * px * rho + 1.) + rho)
    v = v / np.sqrt(px**2 + 2. * px * rho + 1.)
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def SSVI2(x, gamma, sigma, rho, t):
    # Second derivative with respect to x
    theta = sigma * sigma * t
    p = phiSSVI(theta, gamma)
    px = p * x
    v = 0.5 * theta * p * p * (1. - rho * rho)
    v = v / ((px**2 + 2. * px * rho + 1.) *
             np.sqrt(px**2 + 2. * px * rho + 1.))
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def SSVIt(x, gamma, sigma, rho, t):
    # First derivative with respect to t, by central difference
    eps = 0.0001
    ssvitplus = SSVI(x, gamma, sigma, rho, t + eps)
    ssvitminus = SSVI(x, gamma, sigma, rho, t - eps)
    deriv = (ssvitplus - ssvitminus) / 2.0 / eps
    return deriv


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def g(x, gamma, sigma, rho, t):
    w = SSVI(x, gamma, sigma, rho, t)
    w1 = SSVI1(x, gamma, sigma, rho, t)
    w2 = SSVI2(x, gamma, sigma, rho, t)
    xwv = x * w1 / w
    v = (1. - 0.5 * xwv) ** 2 - 0.25 * w1 * w1 * (0.25 + 1. / w) + 0.5 * w2
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def dminus(x, gamma, sigma, rho, t):
    vsqrt = np.sqrt(SSVI(x, gamma, sigma, rho, t))
    v = -x / vsqrt - 0.5 * vsqrt
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def densitySSVI(x, gamma, sigma, rho, t):
    dm = dminus(x, gamma, sigma, rho, t)
    v = g(x, gamma, sigma, rho, t) * np.exp(-0.5 * dm * dm)
    v = v / np.sqrt(2. * np.pi * SSVI(x, gamma, sigma, rho, t))
    return v


@njit(float64(float64, float64, float64, float64, float64),
      fastmath=True, cache=True)
def SSVI_LocalVarg(x, gamma, sigma, rho, t):
    # Compute the equivalent SSVI local variance
    num = SSVIt(x, gamma, sigma, rho, t)
    den = g(x, gamma, sigma, rho, t)
    var = num/den
    return var


@njit(float64(float64[:], float64, float64, float64),
      fastmath=True, cache=True)
def volFunctionSSVI(params, f, k, t):
    ''' Volatility Function proposed by Gatheral in 2004.'''

    gamma = params[0]
    sigma = params[1]
    rho = params[2]
    x = np.log(f/k)

    vart = SSVI_LocalVarg(x, gamma, sigma, rho, t)
    sigma = np.sqrt(vart)
    return sigma

###############################################################################


@njit(float64(float64, float64, float64, float64),
      fastmath=True, cache=True)
def d_1(F, X, vol, t):
    d1 = (math.log(F/X) + 0.5 * (vol ** 2) * t)/(vol * math.sqrt(t))
    return d1


@njit(float64(float64, float64, float64, float64),
      fastmath=True, cache=True)
def d_2(F, X, vol, t):
    d2 = d_1(F, X, vol, t) - vol * math.sqrt(t)
    return d2


@njit(float64(float64[:], float64, float64, float64),
      fastmath=True, cache=True)
def volFunctionVV(params, f, k, t):
    K_P, K_ATM, K_C, sig_PUT, sig_ATM, sig_CALL = params
    z1 = (math.log(K_ATM/k) * math.log(K_C/k)) / \
        (math.log(K_ATM/K_P) * math.log(K_C/K_P))
    z2 = (math.log(k/K_P) * math.log(K_C/k)) / \
        (math.log(K_ATM/K_P) * math.log(K_C/K_ATM))
    z3 = (math.log(k/K_P) * math.log(k/K_ATM)) / \
        (math.log(K_C/K_P) * math.log(K_C/K_ATM))

    First_Ord_Approx = (z1 * sig_PUT + z2 * sig_ATM + z3 * sig_CALL) - sig_ATM
    Second_Ord_Approx = z1 * d_1(f, K_P, sig_PUT, t) * d_2(f, K_P, sig_PUT, t) * ((sig_PUT-sig_ATM)**2) \
        + z2 * d_1(f, K_ATM, sig_ATM, t) * d_2(f, K_ATM, sig_ATM, t) * ((sig_ATM-sig_ATM)**2) \
        + z3 * d_1(f, K_C, sig_CALL, t) * d_2(f, K_C,
                                              sig_CALL, t) * ((sig_CALL-sig_ATM)**2)

    d1_d2 = d_1(f, k, sig_ATM, t) * d_2(f, k, sig_ATM, t)

    vol = sig_ATM + (-sig_ATM + math.sqrt(sig_ATM**2 + d1_d2 *
                                          (2 * sig_ATM * First_Ord_Approx + Second_Ord_Approx)))/(d1_d2)

    return vol
