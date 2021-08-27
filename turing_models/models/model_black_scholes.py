# TODO Fix this

import numpy as np

from turing_models.utilities.global_types import TuringOptionTypes
from turing_models.utilities.error import TuringError

from turing_models.utilities.helper_functions import checkArgumentTypes

from .model import TuringModel
from .model_crr_tree import crrTreeValAvg
from .model_black_scholes_analytical import bawValue
from .model_black_scholes_analytical import bs_value

from enum import Enum

class TuringModelBlackScholesTypes(Enum):
        DEFAULT = 0
        ANALYTICAL = 1
        CRR_TREE = 2
        BARONE_ADESI = 3

###############################################################################

class TuringModelBlackScholes(TuringModel):
    
    def __init__(self,
                 volatility: (float, np.ndarray),
                 implementationType: TuringModelBlackScholesTypes = TuringModelBlackScholesTypes.DEFAULT,
                 numStepsPerYear: int = 252):

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

            if self._implementationType is TuringModelBlackScholesTypes.DEFAULT:
                self._implementationType = TuringModelBlackScholesTypes.ANALYTICAL

            if self._implementationType == TuringModelBlackScholesTypes.ANALYTICAL:

                v =  bs_value(spotPrice, timeToExpiry, strikePrice, 
                             riskFreeRate, dividendRate, self._volatility,
                             optionType.value)

                return v

            elif self._implementationType == TuringModelBlackScholesTypes.CRR_TREE:
                
                v = crrTreeValAvg(spotPrice, riskFreeRate, dividendRate, 
                                  self._volatility, self._numStepsPerYear,
                                  timeToExpiry, optionType.value, 
                                  strikePrice)['value']

                return v

            else:
                
                raise TuringError("Implementation not available for this product")

        elif optionType == TuringOptionTypes.AMERICAN_CALL \
            or optionType == TuringOptionTypes.AMERICAN_PUT:

            if self._implementationType is TuringModelBlackScholesTypes.DEFAULT:
                self._implementationType = TuringModelBlackScholesTypes.CRR_TREE

            if self._implementationType == TuringModelBlackScholesTypes.BARONE_ADESI:

                if optionType == TuringOptionTypes.AMERICAN_CALL:
                    phi = +1
                elif optionType == TuringOptionTypes.AMERICAN_PUT:
                    phi = -1

                v = bawValue(spotPrice, timeToExpiry, strikePrice,
                             riskFreeRate, dividendRate, self._volatility,
                             phi)

                return v

            elif self._implementationType == TuringModelBlackScholesTypes.CRR_TREE:

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

