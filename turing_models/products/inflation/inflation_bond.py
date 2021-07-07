###############################################################################
# ADD Inflation assumption and resulting yield calculation
# Pricing using inflation curve and discount curve
###############################################################################


from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.utilities.global_types import TuringYTMCalcType
from ..bonds.bond import TuringBond

###############################################################################


class TuringInflationBond(TuringBond):
    ''' Class for inflation-linked bonds like TIPS and related analytics. These
    are bonds with coupon and principal adjusted by an index such as the CPI.
    We inherit from the TuringBond class. '''

    def __init__(self,
                 issueDate: TuringDate,
                 maturityDate: TuringDate,
                 coupon: float,  # Annualised bond coupon before inflation
                 freqType: TuringFrequencyTypes,
                 accrualType: TuringDayCountTypes,
                 faceAmount: float,
                 baseCPIValue: float,
                 numExDividendDays: int = 0,
                 convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO): # Value of CPI index at bond issue date
        ''' Create TuringInflationBond object by providing Maturity, Frequency,
        coupon, frequency and the accrual convention type. You must also supply
        the base CPI used for all coupon and principal related calculations.
        The class inherits from TuringBond so has many similar functions. The YTM'''

        checkArgumentTypes(self.__init__, locals())

        if issueDate >= maturityDate:
            raise TuringError("Issue Date must preceded maturity date.")

        self._issueDate = issueDate
        self._maturityDate = maturityDate
        self._coupon = coupon
        self._freqType = freqType
        self._accrualType = accrualType
        self._frequency = TuringFrequency(freqType)
        self._faceAmount = faceAmount  # This is the bond holding size
        self._baseCPIValue = baseCPIValue # CPI value at issue date of bond
        self._par = 100.0  # This is how price is quoted
        self._redemption = 1.0 # Amount paid at maturity
        self._numExDividendDays = numExDividendDays
        if convention not in TuringYTMCalcType:
            raise TuringError("Yield convention unknown." + str(convention))

        self._convention = convention

        self._flowDates = []
        self._flowAmounts = []

        self._settlementDate = TuringDate(1900, 1, 1)
        self._accruedInterest = None
        self._accruedDays = 0.0
        self._alpha = 0.0

        self._calculateFlowDates()
        self._calculateFlowAmounts()

###############################################################################

    def inflationPrincipal(self,
                           settlementDate: TuringDate,
                           ytm: float,
                           referenceCPI: float):
        ''' Calculate the principal value of the bond based on the face
        amount and the CPI growth. '''

        indexRatio = referenceCPI / self._baseCPIValue
        fullPrice = self.fullPriceFromYTM(settlementDate, ytm)
        principal = fullPrice * self._faceAmount / self._par
        principal = principal - self._accruedInterest
        principal *= indexRatio
        return principal

###############################################################################

    def flatPriceFromYieldToMaturity(self,
                                     settlementDate: TuringDate,
                                     ytm: float,
                                     lastCpnCPI: float):
        ''' Calculate the flat clean price value of the bond based on the clean
        price amount and the CPI growth to the last coupon date. '''

        indexRatio = lastCpnCPI / self._baseCPIValue
        cleanPrice = self.cleanPriceFromYTM(settlementDate, ytm)
        flatPrice = cleanPrice * self._faceAmount / self._par
        flatPrice *= indexRatio
        return flatPrice

###############################################################################

    def calcInflationAccruedInterest(self, settlementDate: TuringDate,
                                     referenceCPI):
        ''' Calculate the amount of coupon that has accrued between the
        previous coupon date and the settlement date. This is adjusted by the
        index ratio in line with the CPI growth since the bond base CPI date.
        We assume no ex-dividend period.
        '''

        self.calcAccruedInterest(settlementDate)
        indexRatio = referenceCPI/self._baseCPIValue
        self._inflationAccruedInterest = self._accruedInterest * indexRatio
        return self._inflationAccruedInterest

###############################################################################

    def __repr__(self):
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("ISSUE DATE", self._issueDate)
        s += labelToString("MATURITY DATE", self._maturityDate)
        s += labelToString("COUPON", self._coupon)
        s += labelToString("FREQUENCY", self._freqType)
        s += labelToString("ACCRUAL TYPE", self._accrualType)
        s += labelToString("FACE AMOUNT", self._faceAmount)
        s += labelToString("BASE CPI VALUE", self._baseCPIValue, "")
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)


###############################################################################
