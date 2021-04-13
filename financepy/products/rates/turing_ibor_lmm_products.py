##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

# TODO: Extend to allow term structure of volatility
# TODO: Extend to allow two fixed legs in underlying swap
# TODO: Cash settled swaptions

''' This module implements the LMM in the spot measure. It combines both model
and product specific code - I am not sure if it is better to separate these. At
the moment this seems to work ok.

THIS IS STILL IN PROTOPTYPE MODE. DO NOT USE. '''

import numpy as np

from financepy.turingutils.turing_calendar import TuringCalendarTypes
from financepy.turingutils.turing_calendar import TuringBusDayAdjustTypes
from financepy.turingutils.turing_calendar import TuringDateGenRuleTypes
from financepy.turingutils.turing_day_count import TuringDayCountTypes
from financepy.turingutils.turing_frequency import TuringFrequencyTypes
from financepy.turingutils.turing_day_count import TuringDayCount
from financepy.turingutils.turing_schedule import TuringSchedule
from financepy.turingutils.turing_error import TuringError
from financepy.turingutils.turing_helper_functions import checkArgumentTypes
from financepy.turingutils.turing_date import TuringDate

from financepy.models.turing_model_rates_lmm import LMMSimulateFwds1F
from financepy.models.turing_model_rates_lmm import LMMSimulateFwdsMF
from financepy.models.turing_model_rates_lmm import LMMSimulateFwdsNF
from financepy.models.turing_model_rates_lmm import TuringRateModelLMMModelTypes
from financepy.models.turing_model_rates_lmm import LMMCapFlrPricer

from financepy.turingutils.turing_global_variables import gDaysInYear
from financepy.turingutils.turing_math import ONE_MILLION

from financepy.turingutils.turing_global_types import TuringSwapTypes
from financepy.turingutils.turing_global_types import TuringCapFloorTypes

from financepy.market.volatility.turing_ibor_cap_vol_curve import TuringIborCapVolCurve

###############################################################################


class FinIborLMMProducts():
    ''' This is the class for pricing Ibor products using the LMM. '''

    def __init__(self,
                 settlementDate: TuringDate,
                 maturityDate: TuringDate,
                 floatFrequencyType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 floatDayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Create a European-style swaption by defining the exercise date of
        the swaption, and all of the details of the underlying interest rate
        swap including the fixed coupon and the details of the fixed and the
        floating leg payment schedules. '''

        checkArgumentTypes(self.__init__, locals())

        if settlementDate > maturityDate:
            raise TuringError("Settlement date must be before maturity date")

        ''' Set up the grid for the Ibor rates that are to be simulated. These
        must be consistent with the floating rate leg of the product that is to
        be priced. '''

        self._startDate = settlementDate
        self._gridDates = TuringSchedule(settlementDate,
                                         maturityDate,
                                         floatFrequencyType,
                                         calendarType,
                                         busDayAdjustType,
                                         dateGenRuleType)._generate()

        self._accrualFactors = []
        self._floatDayCountType = floatDayCountType

        basis = TuringDayCount(self._floatDayCountType)
        prevDt = self._gridDates[0]

        self._gridTimes = [0.0]

        for nextDt in self._gridDates[1:]:
            tau = basis.yearFrac(prevDt, nextDt)[0]
            t = (nextDt - self._gridDates[0]) / gDaysInYear
            self._accrualFactors.append(tau)
            self._gridTimes.append(t)
            prevDt = nextDt

#        print(self._gridTimes)
        self._accrualFactors = np.array(self._accrualFactors)
        self._numForwards = len(self._accrualFactors)
        self._fwds = None

#        print("Num FORWARDS", self._numForwards)

###############################################################################

    def simulate1F(self,
                   discountCurve,
                   volCurve: TuringIborCapVolCurve,
                   numPaths: int = 1000,
                   numeraireIndex: int = 0,
                   useSobol: bool = True,
                   seed: int = 42):
        ''' Run the one-factor simulation of the evolution of the forward
        Ibors to generate and store all of the Ibor forward rate paths. '''

        if numPaths < 2 or numPaths > 1000000:
            raise TuringError("NumPaths must be between 2 and 1 million")

        if discountCurve._valuationDate != self._startDate:
            raise TuringError("Curve anchor date not the same as LMM start date.")

        self._numPaths = numPaths
        self._numeraireIndex = numeraireIndex
        self._useSobol = useSobol

        numGridPoints = len(self._gridDates)

        self._numForwards = numGridPoints
        self._forwardCurve = []

        for i in range(1, numGridPoints):
            startDate = self._gridDates[i-1]
            endDate = self._gridDates[i]
            fwdRate = discountCurve.fwdRate(startDate,
                                            endDate,
                                            self._floatDayCountType)
            self._forwardCurve.append(fwdRate)

        self._forwardCurve = np.array(self._forwardCurve)

        gammas = np.zeros(numGridPoints)
        for ix in range(1, numGridPoints):
            dt = self._gridDates[ix]
            gammas[ix] = volCurve.capletVol(dt)

        self._fwds = LMMSimulateFwds1F(self._numForwards,
                                       numPaths,
                                       numeraireIndex,
                                       self._forwardCurve,
                                       gammas,
                                       self._accrualFactors,
                                       useSobol,
                                       seed)

###############################################################################

    def simulateMF(self,
                   discountCurve,
                   numFactors: int,
                   lambdas: np.ndarray,
                   numPaths: int = 10000,
                   numeraireIndex: int = 0,
                   useSobol: bool = True,
                   seed: int = 42):
        ''' Run the simulation to generate and store all of the Ibor forward
        rate paths. This is a multi-factorial version so the user must input
        a numpy array consisting of a column for each factor and the number of
        rows must equal the number of grid times on the underlying simulation
        grid. CHECK THIS. '''

#        checkArgumentTypes(self.__init__, locals())

        if numPaths < 2 or numPaths > 1000000:
            raise TuringError("NumPaths must be between 2 and 1 million")

        if discountCurve._curveDate != self._startDate:
            raise TuringError("Curve anchor date not the same as LMM start date.")

        print("LEN LAMBDAS", len(lambdas))
        print("LEN", len(lambdas[0]))
        # We pass a vector of vol curves, one for each factor
        if numFactors != len(lambdas):
            raise TuringError("Lambda doesn't have specified number of factors.")

        numRows = len(lambdas[0])
        if numRows != self._numForwards+1:
            raise TuringError("Vol Components needs same number of rows as grid")

        self._numPaths = numPaths
        self._numeraireIndex = numeraireIndex
        self._useSobol = useSobol

        self._numForwards = len(self._gridDates) - 1
        self._forwardCurve = []

        for i in range(1, self._numForwards):
            startDate = self._gridDates[i-1]
            endDate = self._gridDates[i]
            fwdRate = discountCurve.fwdRate(startDate, endDate,
                                            self._floatDayCountType)
            self._forwardCurve.append(fwdRate)

        self._forwardCurve = np.array(self._forwardCurve)

        self._fwds = LMMSimulateFwdsMF(self._numForwards,
                                       numFactors,
                                       numPaths,
                                       numeraireIndex,
                                       self._forwardCurve,
                                       lambdas,
                                       self._accrualFactors,
                                       useSobol,
                                       seed)

###############################################################################

    def simulateNF(self,
                   discountCurve,
                   volCurve: TuringIborCapVolCurve,
                   correlationMatrix: np.ndarray,
                   modelType: TuringRateModelLMMModelTypes,
                   numPaths: int = 1000,
                   numeraireIndex: int = 0,
                   useSobol: bool = True,
                   seed: int = 42):
        ''' Run the simulation to generate and store all of the Ibor forward
        rate paths using a full factor reduction of the fwd-fwd correlation
        matrix using Cholesky decomposition.'''

        checkArgumentTypes(self.__init__, locals())

        if numPaths < 2 or numPaths > 1000000:
            raise TuringError("NumPaths must be between 2 and 1 million")

        if isinstance(modelType, TuringRateModelLMMModelTypes) is False:
            raise TuringError("Model type must be type TuringRateModelLMMModelTypes")

        if discountCurve.curveDate != self._startDate:
            raise TuringError("Curve anchor date not the same as LMM start date.")

        self._numPaths = numPaths
        self._volCurves = volCurve
        self._correlationMatrix = correlationMatrix
        self._modelType = modelType
        self._numeraireIndex = numeraireIndex
        self._useSobol = useSobol

        numGridPoints = len(self._gridTimes)

        self._numForwards = numGridPoints - 1
        self._forwardCurve = []

        for i in range(1, numGridPoints):
            startDate = self._gridDates[i-1]
            endDate = self._gridDates[i]
            fwdRate = discountCurve.forwardRate(startDate,
                                                endDate,
                                                self._floatDayCountType)
            self._forwardCurve.append(fwdRate)

        self._forwardCurve = np.array(self._forwardCurve)

        zetas = np.zeros(numGridPoints)
        for ix in range(1, numGridPoints):
            dt = self._gridDates[ix]
            zetas[ix] = volCurve.capletVol(dt)

        # This function does not use Sobol - TODO
        self._fwds = LMMSimulateFwdsNF(self._numForwards,
                                       numPaths,
                                       self._forwardCurve,
                                       zetas,
                                       correlationMatrix,
                                       self._accrualFactors,
                                       seed)

###############################################################################

    def valueSwaption(self,
                      settlementDate: TuringDate,
                      exerciseDate: TuringDate,
                      maturityDate: TuringDate,
                      swaptionType: TuringSwapTypes,
                      fixedCoupon: float,
                      fixedFrequencyType: TuringFrequencyTypes,
                      fixedDayCountType: TuringDayCountTypes,
                      notional: float = ONE_MILLION,
                      floatFrequencyType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                      floatDayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360,
                      calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                      busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                      dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Value a swaption in the LMM model using simulated paths of the
        forward curve. This relies on pricing the fixed leg of the swap and
        assuming that the floating leg will be worth par. As a result we only
        need simulate Ibors with the frequency of the fixed leg. '''

        # Note that the simulation time steps run all the way out to the last
        # forward rate. However we only really need the forward rates at the
        # expiry date of the option. It may be worth amending the simulate
        # code to impose a limit on the time steps in order to speed up the
        # overall pricing if it requires a new run every time. However once
        # generated, the speed of pricing is not affected so this is not
        # strictly an urgent issue.

        swaptionFloatDates = TuringSchedule(settlementDate,
                                            maturityDate,
                                            floatFrequencyType,
                                            calendarType,
                                            busDayAdjustType,
                                            dateGenRuleType)._generate()

        for swaptionDt in swaptionFloatDates:
            foundDt = False
            for gridDt in self._gridDates:
                if swaptionDt == gridDt:
                    foundDt = True
                    break
            if foundDt is False:
                raise TuringError("Swaption float leg not on grid.")

        swaptionFixedDates = TuringSchedule(settlementDate,
                                            maturityDate,
                                            fixedFrequencyType,
                                            calendarType,
                                            busDayAdjustType,
                                            dateGenRuleType)._generate()

        for swaptionDt in swaptionFixedDates:
            foundDt = False
            for gridDt in self._gridDates:
                if swaptionDt == gridDt:
                    foundDt = True
                    break
            if foundDt is False:
                raise TuringError("Swaption fixed leg not on grid.")

        a = 0
        b = 0

        for gridDt in self._gridDates:
            if gridDt == exerciseDate:
                break
            else:
                a += 1

        for gridDt in self._gridDates:
            if gridDt == maturityDate:
                break
            else:
                b += 1

        if b == 0:
            raise TuringError("Swaption swap maturity date is today.")

#        numPaths = 1000
#        v = LMMSwaptionPricer(fixedCoupon, a, b, numPaths,
#                              fwd0, fwds, taus, isPayer)
        v = 0.0
        return v

###############################################################################

    def valueCapFloor(self,
                      settlementDate: TuringDate,
                      maturityDate: TuringDate,
                      capFloorType: TuringCapFloorTypes,
                      capFloorRate: float,
                      frequencyType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                      dayCountType: TuringDayCountTypes = TuringDayCountTypes.ACT_360,
                      notional: float = ONE_MILLION,
                      calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                      busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                      dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Value a cap or floor in the LMM. '''

        capFloorDates = TuringSchedule(settlementDate,
                                       maturityDate,
                                       frequencyType,
                                       calendarType,
                                       busDayAdjustType,
                                       dateGenRuleType)._generate()

        for capFloorletDt in capFloorDates:
            foundDt = False
            for gridDt in self._gridDates:
                if capFloorletDt == gridDt:
                    foundDt = True
                    break
            if foundDt is False:
                raise TuringError("CapFloor date not on grid.")

        numFowards = len(capFloorDates)
        numPaths = self._numPaths
        K = capFloorRate
        isCap = 0
        if capFloorType == TuringCapFloorTypes.CAP:
            isCap = 1

        fwd0 = self._forwardCurve
        fwds = self._fwds
        taus = self._accrualFactors

        v = LMMCapFlrPricer(numFowards, numPaths, K, fwd0, fwds, taus, isCap)

        # Sum the cap/floorlets to get cap/floor value
        v_capFloor = 0.0
        for v_capFloorLet in v:
            v_capFloor += v_capFloorLet * notional

        return v_capFloor

###############################################################################

    def __repr__(self):
        ''' Function to allow us to print the LMM Products details. '''

        s = "Function not written"
        return s

###############################################################################

    def _print(self):
        ''' Alternative print method. '''

        print(self)

###############################################################################
