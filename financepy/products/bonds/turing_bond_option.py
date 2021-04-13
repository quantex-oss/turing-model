##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

from financepy.finutils.turing_global_variables import gDaysInYear
from financepy.finutils.turing_error import TuringError
from financepy.finutils.turing_date import TuringDate
from financepy.finutils.turing_helper_functions import labelToString, checkArgumentTypes
from financepy.market.curves.turing_discount_curve import TuringDiscountCurve
from financepy.finutils.turing_global_types import TuringOptionTypes, TuringExerciseTypes
from financepy.products.bonds.turing_bond import TuringBond

from enum import Enum
import numpy as np

###############################################################################
# TODO: Add BDT model to valuation
# TODO: Reorganise code - too much duplication
###############################################################################


class TuringBondModelTypes(Enum):
    BLACK = 1
    HO_LEE = 2
    HULL_WHITE = 3
    BLACK_KARASINSKI = 4

###############################################################################


class TuringBondOption():
    ''' Class for options on fixed coupon bonds. These are options to either
    buy or sell a bond on or before a specific future expiry date at a strike
    price that is set on trade date. A European option only allows the bond to
    be exercised into on a specific expiry date. An American option allows the
    option holder to exercise early, potentially allowing earlier coupons to
    be received. '''

    def __init__(self,
                 bond: TuringBond,
                 expiryDate: TuringDate,
                 strikePrice: float,
                 faceAmount: float,
                 optionType: TuringOptionTypes):

        checkArgumentTypes(self.__init__, locals())

        self._expiryDate = expiryDate
        self._strikePrice = strikePrice
        self._bond = bond
        self._optionType = optionType
        self._faceAmount = faceAmount

###############################################################################

    def value(self,
              valuationDate: TuringDate,
              discountCurve: TuringDiscountCurve,
              model):
        ''' Value a bond option (option on a bond) using a specified model
        which include the Hull-White, Black-Karasinski and Black-Derman-Toy
        model which are all implemented as short rate tree models. '''

        texp = (self._expiryDate - valuationDate) / gDaysInYear
        tmat = (self._bond._maturityDate - valuationDate) / gDaysInYear

        dfTimes = discountCurve._times
        dfValues = discountCurve._dfs

        # We need all of the flows in case the option is American and some occur before expiry
        flowDates = self._bond._flowDates
        flowAmounts = self._bond._flowAmounts

        couponTimes = []
        couponFlows = []

        numFlows = len(self._bond._flowDates)

        # Want the first flow to be the previous coupon date
        # This is needed to calculate accrued correctly        
        for i in range(1, numFlows):
            pcd = flowDates[i-1]
            ncd = flowDates[i]
            if pcd < valuationDate and ncd > valuationDate:            
                flowTime = (pcd - valuationDate) / gDaysInYear
                couponTimes.append(flowTime)
                couponFlows.append(flowAmounts[i])
                break

        for i in range(1, numFlows):
            if flowDates[i] == valuationDate:
                couponTimes.append(0.0)
                couponFlows.append(flowAmounts[i])
                
        # Now calculate the remaining coupons
        for i in range(1, numFlows):
            ncd = flowDates[i]
            if ncd > valuationDate:            
                flowTime = (ncd - valuationDate) / gDaysInYear
                couponTimes.append(flowTime)
                couponFlows.append(flowAmounts[i])

        ##################################################################

        couponTimes = np.array(couponTimes)
        couponFlows = np.array(couponFlows)

        exerciseType = TuringExerciseTypes.AMERICAN

        if self._optionType == TuringOptionTypes.EUROPEAN_CALL \
            or self._optionType == TuringOptionTypes.EUROPEAN_PUT:
                exerciseType = TuringExerciseTypes.EUROPEAN

        # This is wasteful if the model is Jamshidian but how to do neat design ?
        model.buildTree(tmat, dfTimes, dfValues)

        v = model.bondOption(texp, self._strikePrice, self._faceAmount,
                             couponTimes, couponFlows, exerciseType)

        if self._optionType == TuringOptionTypes.EUROPEAN_CALL \
            or self._optionType == TuringOptionTypes.AMERICAN_CALL:
                return v['call']    
        elif self._optionType == TuringOptionTypes.EUROPEAN_PUT \
            or self._optionType == TuringOptionTypes.AMERICAN_PUT:
                return v['put']
        else:
            print(self._optionType)
            raise TuringError("Unknown option type.")

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("EXPIRY DATE", self._expiryDate)
        s += labelToString("STRIKE", self._strikePrice)
        s += labelToString("OPTION TYPE", self._optionType)
        s += labelToString("FACE AMOUNT", self._faceAmount, "")
        s += "Underlying Bond\n"
        s += str(self._bond)
        return s

###############################################################################

    def _print(self):
        ''' Simple print function for backward compatibility. '''
        print(self)

###############################################################################
