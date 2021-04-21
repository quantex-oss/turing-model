# TODO: Implied volatility
# TODO: Term structure of volatility
# TODO: Check that curve anchor date is valuation date ?

from typing import Optional

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.mathematics import ONE_MILLION
from turing_models.utilities.error import TuringError
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.models.model_black import TuringModelBlack
from turing_models.models.model_black_shifted import TuringModelBlackShifted
from turing_models.models.model_bachelier import TuringModelBachelier
from turing_models.models.model_sabr import TuringModelSABR
from turing_models.models.model_sabr_shifted import TuringModelSABRShifted
from turing_models.models.model_rates_hw import TuringModelRatesHW
from turing_models.utilities.global_types import TuringCapFloorTypes, TuringOptionTypes

##########################################################################

from enum import Enum

class TuringIborCapFloorModelTypes(Enum):
    BLACK = 1
    SHIFTED_BLACK = 2
    SABR = 3

##########################################################################


class TuringIborCapFloor():
    ''' Class for Caps and Floors. These are contracts which observe a Ibor
    reset L on a future start date and then make a payoff at the end of the
    Ibor period which is Max[L-K,0] for a cap and Max[K-L,0] for a floor.
    This is then day count adjusted for the Ibor period and then scaled by
    the contract notional to produce a valuation. A number of models can be
    selected from.'''

    def __init__(self,
                 startDate: TuringDate,
                 maturityDateOrTenor: (TuringDate, str),
                 optionType: TuringCapFloorTypes,
                 strikeRate: float,
                 lastFixing: Optional[float] = None,
                 freqType: TuringFrequencyTypes = TuringFrequencyTypes.QUARTERLY,
                 dayCountType: TuringDayCountTypes = TuringDayCountTypes.THIRTY_E_360_ISDA,
                 notional: float = ONE_MILLION,
                 calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND,
                 busDayAdjustType: TuringBusDayAdjustTypes = TuringBusDayAdjustTypes.FOLLOWING,
                 dateGenRuleType: TuringDateGenRuleTypes = TuringDateGenRuleTypes.BACKWARD):
        ''' Initialise TuringIborCapFloor object. '''

        checkArgumentTypes(self.__init__, locals())

        self._calendarType = calendarType
        self._busDayAdjustType = busDayAdjustType

        if type(maturityDateOrTenor) == TuringDate:
            maturityDate = maturityDateOrTenor
        else:
            maturityDate = startDate.addTenor(maturityDateOrTenor)
            calendar = TuringCalendar(self._calendarType)
            maturityDate = calendar.adjust(maturityDate,
                                           self._busDayAdjustType)

        if startDate > maturityDate:
            raise TuringError("Start date must be before maturity date")

        self._startDate = startDate
        self._maturityDate = maturityDate
        self._optionType = optionType
        self._strikeRate = strikeRate
        self._lastFixing = lastFixing
        self._freqType = freqType
        self._dayCountType = dayCountType
        self._notional = notional
        self._dateGenRuleType = dateGenRuleType

        self._capFloorLetValues = []
        self._capFloorLetAlphas = []
        self._capFloorLetFwdRates = []
        self._capFloorLetIntrinsic = []
        self._capFloorLetDiscountFactors = []
        self._capFloorPV = []

        self._valuationDate = None
        self._dayCounter = None

###############################################################################

    def _generateDates(self):

        schedule = TuringSchedule(self._startDate,
                                  self._maturityDate,
                                  self._freqType,
                                  self._calendarType,
                                  self._busDayAdjustType,
                                  self._dateGenRuleType)

        self._capFloorLetDates = schedule._adjustedDates

##########################################################################

    def value(self, valuationDate, liborCurve, model):
        ''' Value the cap or floor using the chosen model which specifies
        the volatility of the Ibor rate to the cap start date. '''

        self._valuationDate = valuationDate
        self._generateDates()

        self._dayCounter = TuringDayCount(self._dayCountType)
        numOptions = len(self._capFloorLetDates)
        strikeRate = self._strikeRate

        if strikeRate < 0.0:
            raise TuringError("Strike < 0.0")

        if numOptions <= 1:
            raise TuringError("Number of options in capfloor equals 1")

        self._capFloorLetValues = [0]
        self._capFloorLetAlphas = [0]
        self._capFloorLetFwdRates = [0]
        self._capFloorLetIntrinsic = [0]
        self._capFloorLetDiscountFactors = [1.00]
        self._capFloorPV = [0.0]

        capFloorValue = 0.0
        capFloorLetValue = 0.0
        # Value the first caplet or floorlet with known payoff

        startDate = self._startDate
        endDate = self._capFloorLetDates[1]

        if self._lastFixing is None:
            fwdRate = liborCurve.fwdRate(startDate, endDate,
                                         self._dayCountType)
        else:
            fwdRate = self._lastFixing

        alpha = self._dayCounter.yearFrac(startDate, endDate)[0]
        df = liborCurve.df(endDate)

        if self._optionType == TuringCapFloorTypes.CAP:
            capFloorLetValue = df * alpha * max(fwdRate - strikeRate, 0.0)
        elif self._optionType == TuringCapFloorTypes.FLOOR:
            capFloorLetValue = df * alpha * max(strikeRate - fwdRate, 0.0)

        capFloorLetValue *= self._notional
        capFloorValue += capFloorLetValue

        self._capFloorLetFwdRates.append(fwdRate)
        self._capFloorLetValues.append(capFloorLetValue)
        self._capFloorLetAlphas.append(alpha)
        self._capFloorLetIntrinsic.append(capFloorLetValue)
        self._capFloorLetDiscountFactors.append(df)
        self._capFloorPV.append(capFloorValue)

        for i in range(2, numOptions):

            startDate = self._capFloorLetDates[i - 1]
            endDate = self._capFloorLetDates[i]
            alpha = self._dayCounter.yearFrac(startDate, endDate)[0]

            df = liborCurve.df(endDate)
            fwdRate = liborCurve.fwdRate(startDate, endDate,
                                         self._dayCountType)

            if self._optionType == TuringCapFloorTypes.CAP:
                intrinsicValue = df * alpha * max(fwdRate - strikeRate, 0.0)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                intrinsicValue = df * alpha * max(strikeRate - fwdRate, 0.0)

            intrinsicValue *= self._notional

            capFloorLetValue = self.valueCapletFloorLet(valuationDate,
                                                        startDate,
                                                        endDate,
                                                        liborCurve,
                                                        model)

            capFloorValue += capFloorLetValue

            self._capFloorLetFwdRates.append(fwdRate)
            self._capFloorLetValues.append(capFloorLetValue)
            self._capFloorLetAlphas.append(alpha)
            self._capFloorLetIntrinsic.append(intrinsicValue)
            self._capFloorLetDiscountFactors.append(df)
            self._capFloorPV.append(capFloorValue)

        return capFloorValue

###############################################################################

    def valueCapletFloorLet(self,
                            valuationDate,
                            capletStartDate,
                            capletEndDate,
                            liborCurve,
                            model):
        ''' Value the caplet or floorlet using a specific model. '''

        texp = (capletStartDate - self._startDate) / gDaysInYear

        alpha = self._dayCounter.yearFrac(capletStartDate, capletEndDate)[0]

        f = liborCurve.fwdRate(capletStartDate, capletEndDate,
                               self._dayCountType)

        k = self._strikeRate
        df = liborCurve.df(capletEndDate)

        if k == 0.0:
            k = 1e-10

        if isinstance(model, TuringModelBlack):

            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_CALL)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelBlackShifted):

            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_CALL)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelBachelier):

            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_CALL)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelSABR):

            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_CALL)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelSABRShifted):

            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_CALL)
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = model.value(f, k, texp, df,
                                               TuringOptionTypes.EUROPEAN_PUT)

        elif isinstance(model, TuringModelRatesHW):

            tmat = (capletEndDate - valuationDate) / gDaysInYear
            alpha = self._dayCounter.yearFrac(capletStartDate,
                                              capletEndDate)[0]
            strikePrice = 1.0/(1.0 + alpha * self._strikeRate)
            notionalAdj = (1.0 + self._strikeRate * alpha)
            faceAmount = 1.0
            dfTimes = liborCurve._times
            dfValues = liborCurve._dfs

            v = model.optionOnZCB(texp, tmat, strikePrice, faceAmount,
                                  dfTimes, dfValues)

            # we divide by alpha to offset the multiplication above
            if self._optionType == TuringCapFloorTypes.CAP:
                capFloorLetValue = v['put'] * notionalAdj / alpha
            elif self._optionType == TuringCapFloorTypes.FLOOR:
                capFloorLetValue = v['call'] * notionalAdj / alpha

        else:
            raise TuringError("Unknown model type " + str(model))

        capFloorLetValue *= (self._notional * alpha)

        return capFloorLetValue

###############################################################################

    def printLeg(self):
        ''' Prints the cap floor payment amounts. '''

        print("START DATE:", self._startDate)
        print("MATURITY DATE:", self._maturityDate)
        print("OPTION TYPE", str(self._optionType))
        print("STRIKE (%):", self._strikeRate * 100)
        print("FREQUENCY:", str(self._freqType))
        print("DAY COUNT:", str(self._dayCountType))
        print("VALUATION DATE", self._valuationDate)

        if len(self._capFloorLetValues) == 0:
            print("Caplets not calculated.")
            return

        if self._optionType == TuringCapFloorTypes.CAP:
            header = "PAYMENT_DATE     YEAR_FRAC   FWD_RATE    INTRINSIC      "
            header += "     DF    CAPLET_PV       CUM_PV"
        elif self._optionType == TuringCapFloorTypes.FLOOR:
            header = "PAYMENT_DATE     YEAR_FRAC   FWD_RATE    INTRINSIC      "
            header += "     DF    FLRLET_PV       CUM_PV"

        print(header)

        iFlow = 0

        for paymentDate in self._capFloorLetDates[iFlow:]:
            if iFlow == 0:
                print("%15s %10s %9s %12s %12.6f %12s %12s" %
                      (paymentDate, "-", "-", "-",
                       self._capFloorLetDiscountFactors[iFlow], "-", "-"))
            else:
                print("%15s %10.7f %9.5f %12.2f %12.6f %12.2f %12.2f" %
                      (paymentDate,
                       self._capFloorLetAlphas[iFlow],
                       self._capFloorLetFwdRates[iFlow]*100,
                       self._capFloorLetIntrinsic[iFlow],
                       self._capFloorLetDiscountFactors[iFlow],
                       self._capFloorLetValues[iFlow],
                       self._capFloorPV[iFlow]))

            iFlow += 1

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("START DATE", self._startDate)
        s += labelToString("MATURITY DATE", self._maturityDate)
        s += labelToString("STRIKE COUPON", self._strikeRate * 100)
        s += labelToString("OPTION TYPE", str(self._optionType))
        s += labelToString("FREQUENCY", str(self._freqType))
        s += labelToString("DAY COUNT", str(self._dayCountType), "")
        return s

###############################################################################

    def _print(self):
        print(self)

###############################################################################
