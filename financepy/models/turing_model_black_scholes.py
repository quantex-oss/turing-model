##############################################################################
# Copyright (C) 2018, 2019, 2020 Dominic O'Kane
##############################################################################

# TODO Fix this

import numpy as np

from ..finutils.turing_global_types import TuringOptionTypes
from ..finutils.turing_error import TuringError

from ..finutils.turing_helper_functions import checkArgumentTypes

from .turing_model import FinModel
from .turing_model_crr_tree import crrTreeValAvg
from .turing_model_black_scholes_analytical import bawValue
from .turing_model_black_scholes_analytical import bsValue

from enum import Enum

class FinModelBlackScholesTypes(Enum):
        DEFAULT = 0
        ANALYTICAL = 1
        CRR_TREE = 2
        BARONE_ADESI = 3

###############################################################################

class FinModelBlackScholes(FinModel):
    
    def __init__(self,
                 volatility: (float, np.ndarray), 
                 implementationType: FinModelBlackScholesTypes = FinModelBlackScholesTypes.DEFAULT,
                 numStepsPerYear: int = 100):

        checkArgumentTypes(self.__init__, locals())

        self._volatility = volatility
        self._implementationType = implementationType
        self._numStepsPerYear = numStepsPerYear

    def value(self,
              spotPrice: float,
              timeToExpiry: float,
              strikePrice: float,
              riskFreeRate: float,
              dividendRate: float,
              optionType: TuringOptionTypes):

        if optionType == TuringOptionTypes.EUROPEAN_CALL \
            or optionType == TuringOptionTypes.EUROPEAN_PUT:

            if self._implementationType is FinModelBlackScholesTypes.DEFAULT:
                self._implementationType = FinModelBlackScholesTypes.ANALYTICAL

            if self._implementationType == FinModelBlackScholesTypes.ANALYTICAL:

                v =  bsValue(spotPrice, timeToExpiry, strikePrice, 
                             riskFreeRate, dividendRate, self._volatility,
                             optionType.value)

                return v

            elif self._implementationType == FinModelBlackScholesTypes.CRR_TREE:
                
                v = crrTreeValAvg(spotPrice, riskFreeRate, dividendRate, 
                                  self._volatility, self._numStepsPerYear,
                                  timeToExpiry, optionType.value, 
                                  strikePrice)['value']

                return v

            else:
                
                raise TuringError("Implementation not available for this product")

        elif optionType == TuringOptionTypes.AMERICAN_CALL \
            or optionType == TuringOptionTypes.AMERICAN_PUT:

            if self._implementationType is FinModelBlackScholesTypes.DEFAULT:
                self._implementationType = FinModelBlackScholesTypes.CRR_TREE

            if self._implementationType == FinModelBlackScholesTypes.BARONE_ADESI:

                if optionType == TuringOptionTypes.AMERICAN_CALL:
                    phi = +1
                elif optionType == TuringOptionTypes.AMERICAN_PUT:
                    phi = -1

                v =  bawValue(spotPrice, timeToExpiry, strikePrice,
                              riskFreeRate, dividendRate, self._volatility,
                              phi)

                return v

            elif self._implementationType == FinModelBlackScholesTypes.CRR_TREE:

                v = crrTreeValAvg(spotPrice, riskFreeRate, dividendRate, 
                                  self._volatility, self._numStepsPerYear,
                                  timeToExpiry, optionType.value, 
                                  strikePrice)['value']

                return v

            else:
                
                raise TuringError("Implementation not available for this product")

        else:
            
            raise TuringError("Should not be here")

###############################################################################

