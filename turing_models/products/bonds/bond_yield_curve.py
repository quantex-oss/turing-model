import numpy as np
import matplotlib.pyplot as plt

from turing_models.utilities.error import TuringError
from turing_models.utilities.date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.math import scale
from turing_models.utilities.helper_functions import labelToString

from .bond_yield_curve_model import TuringCurveFitPolynomial
from .bond_yield_curve_model import TuringCurveFitNelsonSiegel
from .bond_yield_curve_model import TuringCurveFitNelsonSiegelSvensson
from .bond_yield_curve_model import TuringCurveFitBSpline

from scipy.optimize import curve_fit
from scipy.interpolate import splrep

###############################################################################
# TO DO: CONSTRAIN TAU'S IN NELSON-SIEGEL
###############################################################################


class TuringBondYieldCurve():
    ''' Class to do fitting of the yield curve and to enable interpolation of
    yields. Because yields assume a flat term structure for each bond, this
    class does not allow discounting to be done and so does not inherit from
    TuringDiscountCurve. It should only be used for visualisation and simple
    interpolation but not for full term-structure-consistent pricing. '''

    def __init__(self,
                 settlementDate: TuringDate,
                 bonds: list,
                 ylds: (np.ndarray, list),
                 curveFit):
        ''' Fit the curve to a set of bond yields using the type of curve
        specified. Bounds can be provided if you wish to enforce lower and
        upper limits on the respective model parameters. '''

        self._settlementDate = settlementDate
        self._bonds = bonds
        self._ylds = np.array(ylds)
        self._curveFit = curveFit

        fitType = type(self._curveFit)
        fit = self._curveFit

        yearsToMaturities = []
        for bond in bonds:
            maturityYears = (bond._maturityDate-settlementDate)/gDaysInYear
            yearsToMaturities.append(maturityYears)
        self._yearsToMaturity = np.array(yearsToMaturities)

        if fitType is TuringCurveFitPolynomial:

            d = fit._power
            coeffs = np.polyfit(self._yearsToMaturity, self._ylds, deg=d)
            fit._coeffs = coeffs

        elif fitType is TuringCurveFitNelsonSiegel:

            xdata = self._yearsToMaturity
            ydata = self._ylds

            popt, pcov = curve_fit(self._curveFit._interpolatedYield,
                                   xdata, ydata, bounds=fit._bounds)

            fit._beta1 = popt[0]
            fit._beta2 = popt[1]
            fit._beta3 = popt[2]
            fit._tau = popt[3]

        elif fitType is TuringCurveFitNelsonSiegelSvensson:

            xdata = self._yearsToMaturity
            ydata = self._ylds

            popt, pcov = curve_fit(self._curveFit._interpolatedYield,
                                   xdata, ydata, bounds=fit._bounds)

            fit._beta1 = popt[0]
            fit._beta2 = popt[1]
            fit._beta3 = popt[2]
            fit._beta4 = popt[3]
            fit._tau1 = popt[4]
            fit._tau2 = popt[5]

        elif fitType is TuringCurveFitBSpline:

            xdata = self._yearsToMaturity
            ydata = self._ylds

            ''' Cubic splines as k=3 '''
            spline = splrep(xdata, ydata, k=fit._power, t=fit._knots)
            fit._spline = spline

        else:
            raise TuringError("Unrecognised curve fit type.")

###############################################################################

    def interpolatedYield(self,
                          maturityDate: TuringDate):

        if type(maturityDate) is TuringDate:
            t = (maturityDate - self._settlementDate) / gDaysInYear
        elif type(maturityDate) is list:
            t = maturityDate
        elif type(maturityDate) is np.ndarray:
            t = maturityDate
        elif type(maturityDate) is float or type(maturityDate) is np.float64:
            t = maturityDate
        else:
            raise TuringError("Unknown date type.")

        fit = self._curveFit

        if type(fit) == TuringCurveFitPolynomial:
            yld = fit._interpolatedYield(t)
        elif type(fit) == TuringCurveFitNelsonSiegel:
            yld = fit._interpolatedYield(t,
                                         fit._beta1,
                                         fit._beta2,
                                         fit._beta3,
                                         fit._tau)

        elif type(fit) == TuringCurveFitNelsonSiegelSvensson:
            yld = fit._interpolatedYield(t,
                                         fit._beta1,
                                         fit._beta2,
                                         fit._beta3,
                                         fit._beta4,
                                         fit._tau1,
                                         fit._tau2)

        elif type(fit) == TuringCurveFitBSpline:
            yld = fit._interpolatedYield(t)

        return yld

###############################################################################

    def plot(self,
             title):
        ''' Display yield curve. '''

        plt.figure(figsize=(12, 6))
        plt.title(title)
        bond_ylds_scaled = scale(self._ylds, 100.0)
        plt.plot(self._yearsToMaturity, bond_ylds_scaled, 'o')
        plt.xlabel('Time to Maturity (years)')
        plt.ylabel('Yield To Maturity (%)')

        tmax = np.max(self._yearsToMaturity)
        t = np.linspace(0.0, int(tmax+0.5), 100)

        yld = self.interpolatedYield(t)
        yld = scale(yld, 100.0)
        plt.plot(t, yld, label=str(self._curveFit))
        plt.legend(loc='lower right')
        plt.ylim((min(yld)-0.3, max(yld)*1.1))
        plt.grid(True)

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("SETTLEMENT DATE", self._settlementDate)
        s += labelToString("BOND", self._bonds)
        s += labelToString("YIELDS", self._ylds)
        s += labelToString("CURVE FIT", self._curveFit)
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

##############################################################################
