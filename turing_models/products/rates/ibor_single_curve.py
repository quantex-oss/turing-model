import numpy as np
from scipy import optimize

from scipy.interpolate import CubicSpline
from scipy.interpolate import PchipInterpolator

import copy

from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.helper_functions import checkArgumentTypes, _funcName
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.market.curves.interpolator import TuringInterpTypes, TuringInterpolator
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.products.rates.ibor_deposit import TuringIborDeposit
from turing_models.products.rates.ibor_fra import TuringIborFRA
from turing_models.products.rates.ibor_swap import TuringIborSwap

swaptol = 1e-10

##############################################################################
# TODO: CHANGE times to dfTimes
##############################################################################


def _f(df, *args):
    ''' Root search objective function for IRS '''

    curve = args[0]
    valueDate = args[1]
    swap = args[2]
    numPoints = len(curve._times)
    curve._dfs[numPoints - 1] = df

    # For curves that need a fit function, we fit it now
    curve._interpolator.fit(curve._times, curve._dfs)
    swap.libor_curve = curve
    # v_swap = swap.value(valueDate, curve, curve, None)
    v_swap = swap.price()
    notional = swap.fixed_leg._notional
    v_swap /= notional
    return v_swap

###############################################################################


def _g(df, *args):
    ''' Root search objective function for swaps '''
    curve = args[0]
    valueDate = args[1]
    fra = args[2]
    numPoints = len(curve._times)
    curve._dfs[numPoints - 1] = df

    # For curves that need a fit function, we fit it now
    curve._interpolator.fit(curve._times, curve._dfs)
    v_fra = fra.value(valueDate, curve)
    v_fra /= fra._notional
    return v_fra

###############################################################################


def _costFunction(dfs, *args):
    ''' Root search objective function for swaps '''

#    print("Discount factors:", dfs)

    liborCurve = args[0]
    valuationDate = liborCurve._valuationDate
    liborCurve._dfs = dfs

    times = liborCurve._times
    values = -np.log(dfs)

    # For curves that need a fit function, we fit it now
    liborCurve._interpolator.fit(liborCurve._times, liborCurve._dfs)

    if liborCurve._interpType == TuringInterpTypes.CUBIC_SPLINE_LOGDFS:
        liborCurve._splineFunction = CubicSpline(times, values)
    elif liborCurve._interpType == TuringInterpTypes.PCHIP_CUBIC_SPLINE:
        liborCurve._splineFunction = PchipInterpolator(times, values)

    cost = 0.0
    for depo in liborCurve._usedDeposits:
        v = depo.value(valuationDate, liborCurve) / depo._notional
#        print("DEPO:", depo._maturityDate, v)
        cost += (v-1.0)**2

    for fra in liborCurve._usedFRAs:
        v = fra.value(valuationDate, liborCurve) / fra._notional
#        print("FRA:", fra._maturityDate, v)
        cost += v*v

    for swap in liborCurve._usedSwaps:
        v = swap.value(valuationDate, liborCurve) / swap._notional
#        print("SWAP:", swap._maturityDate, v)
        cost += v*v

    print("Cost:", cost)
    return cost

###############################################################################


class TuringIborSingleCurve(TuringDiscountCurve):
    ''' Constructs one discount and index curve as implied by prices of Ibor
    deposits, FRAs and IRS. Discounting is assumed to be at Libor and the value
    of the floating leg (including a notional) is assumed to be par. This
    approach has been overtaken since 2008 as OIS discounting has become the
    agreed discounting approach for ISDA derivatives. This curve method is
    therefore intended for those happy to assume simple Libor discounting.

    The curve date is the date on which we are performing the valuation based
    on the information available on the curve date. Typically it is the date on
    which an amount of 1 unit paid has a present value of 1. This class
    inherits from TuringDiscountCurve and so it has all of the methods that that
    class has.

    There are two main curve-building approaches:

    1) The first uses a bootstrap that interpolates swap rates linearly for
    coupon dates that fall between the swap maturity dates. With this, we can
    solve for the discount factors iteratively without need of a solver. This
    will give us a set of discount factors on the grid dates that refit the
    market exactly. However, when extracting discount factors, we will then
    assume flat forward rates between these coupon dates. There is no
    contradiction as it is as though we had been quoted a swap curve with all
    of the market swap rates, and with an additional set as though the market
    quoted swap rates at a higher frequency than the market.

    2) The second uses a bootstrap that uses only the swap rates provided but
    which also assumes that forwards are flat between these swap maturity
    dates. This approach is non-linear and so requires a solver. Consequently
    it is slower. Its advantage is that we can switch interpolation schemes
    to provide a smoother or other functional curve shape which may have a more
    economically justifiable shape. However the root search makes it slower.'''

###############################################################################

    def __init__(self,
                 valuationDate: TuringDate,  # This is the trade date (not T+2)
                 iborDeposits: list,
                 iborFRAs: list,
                 iborSwaps: list,
                 interpType: TuringInterpTypes = TuringInterpTypes.LINEAR_ZERO_RATES,
                 checkRefit: bool = False):  # Set to True to test it works
        ''' Create an instance of a FinIbor curve given a valuation date and
        a set of ibor deposits, ibor FRAs and iborSwaps. Some of these may
        be left None and the algorithm will just use what is provided. An
        interpolation method has also to be provided. The default is to use a
        linear interpolation for swap rates on coupon dates and to then assume
        flat forwards between these coupon dates.

        The curve will assign a discount factor of 1.0 to the valuation date.
        If no instrument is starting on the valuation date, the curve is then
        assumed to be flat out to the first instrument using its zero rate.
        '''

        checkArgumentTypes(getattr(self, _funcName(), None), locals())

        self._valuationDate = valuationDate
        self._validateInputs(iborDeposits, iborFRAs, iborSwaps)
        self._interpType = interpType
        self._checkRefit = checkRefit
        self._interpolator = None
        self._buildCurve()

###############################################################################

    def _buildCurve(self):
        ''' Build curve based on interpolation. '''

        self._buildCurveUsing1DSolver()

###############################################################################

    def _validateInputs(self,
                        iborDeposits,
                        iborFRAs,
                        iborSwaps):
        ''' Validate the inputs for each of the Ibor products. '''

        numDepos = len(iborDeposits)
        numFRAs = len(iborFRAs)
        numSwaps = len(iborSwaps)

        depoStartDate = self._valuationDate
        swapStartDate = self._valuationDate

        if numDepos + numFRAs + numSwaps == 0:
            raise TuringError("No calibration instruments.")

        # Validation of the inputs.
        if numDepos > 0:

            depoStartDate = iborDeposits[0]._startDate

            for depo in iborDeposits:

                if isinstance(depo, TuringIborDeposit) is False:
                    raise TuringError(
                        "Deposit is not of type TuringIborDeposit")

                startDate = depo._startDate

                if startDate < self._valuationDate:
                    raise TuringError(
                        "First deposit starts before valuation date.")

                if startDate < depoStartDate:
                    depoStartDate = startDate

            for depo in iborDeposits:
                startDt = depo._startDate
                endDt = depo.maturity_date
                if startDt >= endDt:
                    raise TuringError(
                        "First deposit ends on or before it begins")

        # Ensure order of depos
        if numDepos > 1:

            prevDt = iborDeposits[0].maturity_date
            for depo in iborDeposits[1:]:
                nextDt = depo.maturity_date
                if nextDt <= prevDt:
                    raise TuringError(
                        "Deposits must be in increasing maturity")
                prevDt = nextDt

        # REMOVED THIS AS WE WANT TO ANCHOR CURVE AT VALUATION DATE
        # USE A SYNTHETIC DEPOSIT TO BRIDGE GAP FROM VALUE DATE TO SETTLEMENT DATE
        # Ensure that valuation date is on or after first deposit start date
        # if numDepos > 1:
        #    if iborDeposits[0]._effectiveDate > self._valuationDate:
        #        raise TuringError("Valuation date must not be before first deposit settles.")

        if numFRAs > 0:
            for fra in iborFRAs:
                if isinstance(fra, TuringIborFRA) is False:
                    raise TuringError("FRA is not of type TuringIborFRA")

                startDt = fra._startDate
                if startDt < self._valuationDate:
                    raise TuringError("FRAs starts before valuation date")

        if numFRAs > 1:
            prevDt = iborFRAs[0].maturity_date
            for fra in iborFRAs[1:]:
                nextDt = fra.maturity_date
                if nextDt <= prevDt:
                    raise TuringError("FRAs must be in increasing maturity")
                prevDt = nextDt

        if numSwaps > 0:

            swapStartDate = iborSwaps[0].effective_date

            for swap in iborSwaps:

                # if (isinstance(swap, TuringIborSwap) or isinstance(swap, IRS)) is False: # is False and isinstance(swap, TuringIborSwap) is False:
                #     raise TuringError("Swap is not of type TuringIborSwap")

                startDt = swap.effective_date
                if startDt < self._valuationDate:
                    raise TuringError("Swaps starts before valuation date.")

                if swap.effective_date < swapStartDate:
                    swapStartDate = swap.effective_date

        if numSwaps > 1:

            # Swaps must all start on the same date for the bootstrap
            startDt = iborSwaps[0].effective_date
            for swap in iborSwaps[1:]:
                nextStartDt = swap.effective_date
                if nextStartDt != startDt:
                    raise TuringError("Swaps must all have same start date.")

            # Swaps must be increasing in tenor/maturity
            prevDt = iborSwaps[0].maturity_date
            for swap in iborSwaps[1:]:
                nextDt = swap.maturity_date
                if nextDt <= prevDt:
                    raise TuringError("Swaps must be in increasing maturity")
                prevDt = nextDt

            # Swaps must have same cashflows for bootstrap to work
            longestSwap = iborSwaps[-1]

            longestSwapCpnDates = longestSwap.fixed_leg._paymentDates

            for swap in iborSwaps[0:-1]:

                swapCpnDates = swap.fixed_leg._paymentDates

                numFlows = len(swapCpnDates)
                for iFlow in range(0, numFlows):
                    if swapCpnDates[iFlow] != longestSwapCpnDates[iFlow]:
                        raise TuringError(
                            "Swap coupons are not on the same date grid.")

        #######################################################################
        # Now we have ensure they are in order check for overlaps and the like
        #######################################################################

        lastDepositMaturityDate = TuringDate(1900, 1, 1)
        firstFRAMaturityDate = TuringDate(1900, 1, 1)
        lastFRAMaturityDate = TuringDate(1900, 1, 1)

        if numDepos > 0:
            lastDepositMaturityDate = iborDeposits[-1].maturity_date

        if numFRAs > 0:
            firstFRAMaturityDate = iborFRAs[0].maturity_date
            lastFRAMaturityDate = iborFRAs[-1].maturity_date

        if numSwaps > 0:
            firstSwapMaturityDate = iborSwaps[0].maturity_date

        if numDepos > 0 and numFRAs > 0:
            if firstFRAMaturityDate <= lastDepositMaturityDate:
                print("FRA Maturity Date:", firstFRAMaturityDate)
                print("Last Deposit Date:", lastDepositMaturityDate)
                raise TuringError("First FRA must end after last Deposit")

        if numFRAs > 0 and numSwaps > 0:
            if firstSwapMaturityDate <= lastFRAMaturityDate:
                raise TuringError("First Swap must mature after last FRA ends")

        # If both depos and swaps start after T, we need a rate to get them to
        # the first deposit. So we create a synthetic deposit rate contract.

        if swapStartDate > self._valuationDate:

            if numDepos == 0:
                raise TuringError("Need a deposit rate to pin down short end.")

            if depoStartDate > self._valuationDate:
                firstDepo = iborDeposits[0]
                if firstDepo._startDate > self._valuationDate:
                    syntheticDeposit = copy.deepcopy(firstDepo)
                    syntheticDeposit._startDate = self._valuationDate
                    syntheticDeposit.maturity_date = firstDepo._startDate
                    iborDeposits.insert(0, syntheticDeposit)
                    numDepos += 1

        # Now determine which instruments are used
        self._usedDeposits = iborDeposits
        self._usedFRAs = iborFRAs
        self._usedSwaps = iborSwaps
        self._dayCountType = None

###############################################################################

    def _buildCurveUsing1DSolver(self):
        ''' Construct the discount curve using a bootstrap approach. This is
        the non-linear slower method that allows the user to choose a number
        of interpolation approaches between the swap rates and other rates. It
        involves the use of a solver. '''

        self._interpolator = TuringInterpolator(self._interpType)
        self._times = np.array([])
        self._dfs = np.array([])

        # time zero is now.
        tmat = 0.0
        dfMat = 1.0
        self._times = np.append(self._times, 0.0)
        self._dfs = np.append(self._dfs, dfMat)
        self._interpolator.fit(self._times, self._dfs)

        for depo in self._usedDeposits:
            dfSettle = self.df(depo._startDate)
            dfMat = depo._maturityDf() * dfSettle
            tmat = (depo.maturity_date - self._valuationDate) / gDaysInYear
            self._times = np.append(self._times, tmat)
            self._dfs = np.append(self._dfs, dfMat)
            self._interpolator.fit(self._times, self._dfs)

        oldtmat = tmat

        for fra in self._usedFRAs:

            tset = (fra._startDate - self._valuationDate) / gDaysInYear
            tmat = (fra.maturity_date - self._valuationDate) / gDaysInYear

            # if both dates are after the previous FRA/FUT then need to
            # solve for 2 discount factors simultaneously using root search

            if tset < oldtmat and tmat > oldtmat:
                dfMat = fra.maturityDf(self)
                self._times = np.append(self._times, tmat)
                self._dfs = np.append(self._dfs, dfMat)
            else:
                self._times = np.append(self._times, tmat)
                self._dfs = np.append(self._dfs, dfMat)
                argtuple = (self, self._valuationDate, fra)
                dfMat = optimize.newton(_g, x0=dfMat, fprime=None,
                                        args=argtuple, tol=swaptol,
                                        maxiter=50, fprime2=None)

        for swap in self._usedSwaps:
            # I use the lastPaymentDate in case a date has been adjusted fwd
            # over a holiday as the maturity date is usually not adjusted CHECK
            maturityDate = swap.fixed_leg._paymentDates[-1]
            tmat = (maturityDate - self._valuationDate) / gDaysInYear

            self._times = np.append(self._times, tmat)
            self._dfs = np.append(self._dfs, dfMat)

            argtuple = (self, self._valuationDate, swap)

            dfMat = optimize.newton(_f, x0=dfMat, fprime=None, args=argtuple,
                                    tol=swaptol, maxiter=50, fprime2=None,
                                    full_output=False)
            # swap.index_curve = None

        if self._checkRefit is True:
            self._checkRefits(1e-10, swaptol, 1e-5)

###############################################################################

    def _buildCurveUsingQuadraticMinimiser(self):
        ''' Construct the discount curve using a minimisation approach. This is
        the This enables a more complex interpolation scheme. '''

        tmat = 0.0
        dfMat = 1.0

        gridTimes = [tmat]
        gridDfs = [dfMat]

        for depo in self._usedDeposits:
            tmat = (depo.maturity_date - self._valuationDate) / gDaysInYear
            gridTimes.append(tmat)

        for fra in self._usedFRAs:
            tmat = (fra.maturity_date - self._valuationDate) / gDaysInYear
            gridTimes.append(tmat)
            gridDfs.append(dfMat)

        for swap in self._usedSwaps:
            tmat = (swap.maturity_date - self._valuationDate) / gDaysInYear
            gridTimes.append(tmat)

        self._times = np.array(gridTimes)
        self._dfs = np.exp(-self._times * 0.05)

        argtuple = (self)

        res = optimize.minimize(_costFunction, self._dfs, method='BFGS',
                                args=argtuple, options={'gtol': 1e-3})

        self._dfs = np.array(res.x)

        if self._checkRefit is True:
            self._checkRefits(1e-10, swaptol, 1e-5)

###############################################################################

    def _buildCurveLinearSwapRateInterpolation(self):
        ''' Construct the discount curve using a bootstrap approach. This is
        the linear swap rate method that is fast and exact as it does not
        require the use of a solver. It is also market standard. '''

        self._interpolator = TuringInterpolator(self._interpType)

        self._times = np.array([])
        self._dfs = np.array([])

        # time zero is now.
        tmat = 0.0
        dfMat = 1.0
        self._times = np.append(self._times, 0.0)
        self._dfs = np.append(self._dfs, dfMat)
        self._interpolator.fit(self._times, self._dfs)

        for depo in self._usedDeposits:
            dfSettle = self.df(depo._startDate)
            dfMat = depo._maturityDf() * dfSettle
            tmat = (depo.maturity_date - self._valuationDate) / gDaysInYear
            self._times = np.append(self._times, tmat)
            self._dfs = np.append(self._dfs, dfMat)
            self._interpolator.fit(self._times, self._dfs)

        oldtmat = tmat

        for fra in self._usedFRAs:

            tset = (fra._startDate - self._valuationDate) / gDaysInYear
            tmat = (fra.maturity_date - self._valuationDate) / gDaysInYear

            # if both dates are after the previous FRA/FUT then need to
            # solve for 2 discount factors simultaneously using root search

            if tset < oldtmat and tmat > oldtmat:
                dfMat = fra.maturityDf(self)
                self._times = np.append(self._times, tmat)
                self._dfs = np.append(self._dfs, dfMat)
                self._interpolator.fit(self._times, self._dfs)

            else:
                self._times = np.append(self._times, tmat)
                self._dfs = np.append(self._dfs, dfMat)
                self._interpolator.fit(self._times, self._dfs)

                argtuple = (self, self._valuationDate, fra)
                dfMat = optimize.newton(_g, x0=dfMat, fprime=None,
                                        args=argtuple, tol=swaptol,
                                        maxiter=50, fprime2=None)

        if len(self._usedSwaps) == 0:
            if self._checkRefit is True:
                self._checkRefits(1e-10, swaptol, 1e-5)
            return

        #######################################################################
        # ADD SWAPS TO CURVE
        #######################################################################

        # Find where the FRAs and Depos go up to as this bit of curve is done
        foundStart = False
        lastDate = self._valuationDate
        if len(self._usedDeposits) != 0:
            lastDate = self._usedDeposits[-1].maturity_date

        if len(self._usedFRAs) != 0:
            lastDate = self._usedFRAs[-1].maturity_date

        # We use the longest swap assuming it has a superset of ALL of the
        # swap flow dates used in the curve construction
        longestSwap = self._usedSwaps[-1]
        couponDates = longestSwap._adjustedFixedDates
        numFlows = len(couponDates)

        # Find where first coupon without discount factor starts
        startIndex = 0
        for i in range(0, numFlows):
            if couponDates[i] > lastDate:
                startIndex = i
                foundStart = True
                break

        if foundStart is False:
            raise TuringError(
                "Found start is false. Swaps payments inside FRAs")

        swapRates = []
        swapTimes = []

        # I use the last coupon date for the swap rate interpolation as this
        # may be different from the maturity date due to a holiday adjustment
        # and the swap rates need to align with the coupon payment dates
        for swap in self._usedSwaps:
            swapRate = swap.fixed_leg._coupon
            maturityDate = swap._adjustedFixedDates[-1]
            tswap = (maturityDate - self._valuationDate) / gDaysInYear
            swapTimes.append(tswap)
            swapRates.append(swapRate)

        interpolatedSwapRates = [0.0]
        interpolatedSwapTimes = [0.0]

        for dt in couponDates[1:]:
            swapTime = (dt - self._valuationDate) / gDaysInYear
            swapRate = np.interp(swapTime, swapTimes, swapRates)
            interpolatedSwapRates.append(swapRate)
            interpolatedSwapTimes.append(swapTime)

        # Do I need this line ?
        interpolatedSwapRates[0] = interpolatedSwapRates[1]

        accrualFactors = longestSwap._fixedYearFracs

        acc = 0.0
        df = 1.0
        pv01 = 0.0
        dfSettle = self.df(longestSwap.effective_date)

        for i in range(1, startIndex):
            dt = couponDates[i]
            df = self.df(dt)
            acc = accrualFactors[i-1]
            pv01 += acc * df

        for i in range(startIndex, numFlows):

            dt = couponDates[i]
            tmat = (dt - self._valuationDate) / gDaysInYear
            swapRate = interpolatedSwapRates[i]
            acc = accrualFactors[i-1]
            pv01End = (acc * swapRate + 1.0)

            dfMat = (dfSettle - swapRate * pv01) / pv01End

            self._times = np.append(self._times, tmat)
            self._dfs = np.append(self._dfs, dfMat)
            self._interpolator.fit(self._times, self._dfs)

            pv01 += acc * dfMat

        if self._checkRefit is True:
            self._checkRefits(1e-10, swaptol, 1e-5)

###############################################################################

    def _checkRefits(self, depoTol, fraTol, swapTol):
        ''' Ensure that the Ibor curve refits the calibration instruments. '''
        for depo in self._usedDeposits:
            v = depo.value(self._valuationDate, self) / depo._notional
            if abs(v - 1.0) > depoTol:
                print("Value", v)
                raise TuringError("Deposit not repriced.")

        for fra in self._usedFRAs:
            v = fra.value(self._valuationDate, self, self) / fra._notional
            if abs(v) > fraTol:
                print("Value", v)
                raise TuringError("FRA not repriced.")

        for swap in self._usedSwaps:
            # We value it as of the start date of the swap
            v = swap.value(swap.effective_date, self, self, None)
            v = v / swap.fixed_leg._notional
#            print("REFIT SWAP VALUATION:", swap._adjustedMaturityDate, v)
            if abs(v) > swapTol:
                print("Swap with maturity " + str(swap.maturity_date)
                      + " Not Repriced. Has Value", v)
                swap.printFixedLegPV()
                swap.printFloatLegPV()
                raise TuringError("Swap not repriced.")

###############################################################################

    def __repr__(self):
        ''' Print out the details of the Ibor curve. '''

        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("VALUATION DATE", self._valuationDate)

        for depo in self._usedDeposits:
            s += to_string("DEPOSIT", "")
            s += depo.__repr__()

        for fra in self._usedFRAs:
            s += to_string("FRA", "")
            s += fra.__repr__()

        for swap in self._usedSwaps:
            s += to_string("SWAP", "")
            s += swap.__repr__()

        numPoints = len(self._times)

        s += to_string("INTERP TYPE", self._interpType)

        s += to_string("GRID TIMES", "GRID DFS")
        for i in range(0, numPoints):
            s += to_string("% 10.6f" % self._times[i],
                           "%12.10f" % self._dfs[i])

        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
