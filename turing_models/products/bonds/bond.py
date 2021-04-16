###############################################################################
# TODO: - ROUNDING CONVENTIONS FOR ACCRUED
# TODO: - CHECK OAS CALCULATION
# TODO:  - Check how first coupon on floating leg is sized on asset swaps. '''
###############################################################################

# https://www.dmo.gov.uk/media/15004/convention_changes.pdf

###############################################################################
# Conventions:
#  GILTS - SEMI ANNUAL ACT/ACT
#  US TREASURIES
###############################################################################

###############################################################################
# NOTE THAT I ASSUME THAT IF YOU SETTLE A SWAP ON A COUPON PAYMENT DATE YOU
# GET THE COUPON AND THE ACCRUED INTEREST EQUALS THE COUPON.
###############################################################################

import numpy as np

from turing_models.utilities.date import TuringDate
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.global_variables import gDaysInYear, gSmall
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.calendar import TuringBusDayAdjustTypes
from turing_models.utilities.calendar import TuringDateGenRuleTypes
from turing_models.utilities.helper_functions import labelToString, checkArgumentTypes
from turing_models.market.curves.discount_curve import TuringDiscountCurve

from scipy import optimize

# References https://www.dmo.gov.uk/media/15011/yldeqns_v1.pdf
# DO TRUE YIELD
# JAPANESE SIMPLE YIELD

###############################################################################


from enum import Enum


class TuringYTMCalcType(Enum):
    UK_DMO = 1,
    US_STREET = 2,
    US_TREASURY = 3

###############################################################################


def _f(y, *args):
    ''' Function used to do root search in price to yield calculation. '''
    bond = args[0]
    settlementDate = args[1]
    price = args[2]
    convention = args[3]
    px = bond.fullPriceFromYTM(settlementDate, y, convention)
    objFn = px - price
    return objFn

###############################################################################


def _g(oas, *args):
    ''' Function used to do root search in price to OAS calculation. '''
    bond = args[0]
    settlementDate = args[1]
    price = args[2]
    discountCurve = args[3]
    px = bond.fullPriceFromOAS(settlementDate, discountCurve, oas)
    objFn = px - price
    return objFn

###############################################################################


class TuringBond(object):
    ''' Class for fixed coupon bonds and performing related analytics. These
    are bullet bonds which means they have regular coupon payments of a known
    size that are paid on known dates plus a payment of par at maturity. '''

    def __init__(self,
                 issueDate: TuringDate,
                 maturityDate: TuringDate,
                 coupon: float,  # Annualised bond coupon
                 freqType: TuringFrequencyTypes,
                 accrualType: TuringDayCountTypes,
                 faceAmount: float = 100.0):
        ''' Create TuringBond object by providing the issue date, maturity Date,
        coupon frequency, annualised coupon, the accrual convention type, face
        amount and the number of ex-dividend days. '''

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
        self._par = 100.0  # This is how price is quoted and amount at maturity
        self._redemption = 1.0 # This is amount paid at maturity

        self._flowDates = []
        self._flowAmounts = []

        self._accruedInterest = None
        self._accruedDays = 0.0
        self._alpha = 0.0

        self._calculateFlowDates()
        self._calculateFlowAmounts()

###############################################################################

    def _calculateFlowDates(self):
        ''' Determine the bond cashflow payment dates.'''

        # This should only be called once from init 

        calendarType = TuringCalendarTypes.NONE
        busDayRuleType = TuringBusDayAdjustTypes.NONE
        dateGenRuleType = TuringDateGenRuleTypes.BACKWARD

        self._flowDates = TuringSchedule(self._issueDate,
                                         self._maturityDate,
                                         self._freqType,
                                         calendarType,
                                         busDayRuleType,
                                         dateGenRuleType)._generate()

###############################################################################

    def _calculateFlowAmounts(self):
        ''' Determine the bond cashflow payment amounts without principal '''

        self._flowAmounts = [0.0]

        for _ in self._flowDates[1:]:
           cpn = self._coupon / self._frequency
           self._flowAmounts.append(cpn)
    
###############################################################################

    def fullPriceFromYTM(self,
                         settlementDate: TuringDate,
                         ytm: float,
                         convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the full price of bond from its yield to maturity. This
        function is vectorised with respect to the yield input. It implements
        a number of standard conventions for calculating the YTM. '''

        if convention not in TuringYTMCalcType:
            raise TuringError("Yield convention unknown." + str(convention))

        self.calcAccruedInterest(settlementDate)

        ytm = np.array(ytm)  # VECTORIZED
        ytm = ytm + 0.000000000012345  # SNEAKY LOW-COST TRICK TO AVOID y=0

        f = TuringFrequency(self._freqType)
        c = self._coupon
        v = 1.0 / (1.0 + ytm/f)

        # n is the number of flows after the next coupon         
        n = 0
        for dt in self._flowDates:
            if dt > settlementDate:
                n += 1
        n = n - 1

        if n < 0:
            raise TuringError("No coupons left")
 
        if convention == TuringYTMCalcType.UK_DMO:
            if n == 0:
                fp = (v**(self._alpha))*(self._redemption + c/f)
            else:
                term1 = (c/f)
                term2 = (c/f)*v
                term3 = (c/f)*v*v*(1.0-v**(n-1))/(1.0-v)
                term4 = self._redemption * (v**n)
                fp = (v**(self._alpha))*(term1 + term2 + term3 + term4)
        elif convention == TuringYTMCalcType.US_TREASURY:
            if n == 0:
                fp = (v**(self._alpha))*(self._redemption + c/f)
            else:
                term1 = (c/f)
                term2 = (c/f)*v
                term3 = (c/f)*v*v*(1.0-v**(n-1))/(1.0-v)
                term4 = self._redemption * (v**n)
                vw = 1.0 / (1.0 + self._alpha * ytm/f)
                fp = (vw)*(term1 + term2 + term3 + term4)
        elif convention == TuringYTMCalcType.US_STREET:
            vw = 1.0 / (1.0 + self._alpha * ytm/f)
            if n == 0:
                vw = 1.0 / (1.0 + self._alpha * ytm/f)
                fp = vw*(self._redemption + c/f)
            else:
                term1 = (c/f)
                term2 = (c/f)*v
                term3 = (c/f)*v*v*(1.0-v**(n-1)) / (1.0-v)
                term4 = self._redemption * (v**n)
                fp = (v**(self._alpha))*(term1 + term2 + term3 + term4)
        else:
            raise TuringError("Unknown yield convention")

        return fp * self._par

###############################################################################

    def principal(self,
                  settlementDate: TuringDate,
                  y: float,
                  convention: TuringYTMCalcType):
        ''' Calculate the principal value of the bond based on the face
        amount from its discount margin and making assumptions about the
        future Ibor rates. '''

        fullPrice = self.fullPriceFromYTM(settlementDate, y, convention)

        principal = fullPrice * self._faceAmount / self._par
        principal = principal - self._accruedInterest
        return principal

###############################################################################

    def dollarDuration(self,
                       settlementDate: TuringDate,
                       ytm: float,
                       convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the risk or dP/dy of the bond by bumping. This is also
        known as the DV01 in Bloomberg. '''

        dy = 0.0001 # 1 basis point
        p0 = self.fullPriceFromYTM(settlementDate, ytm - dy, convention)
        p2 = self.fullPriceFromYTM(settlementDate, ytm + dy, convention)
        durn = -(p2 - p0) / dy / 2.0
        return durn

###############################################################################

    def macauleyDuration(self,
                         settlementDate: TuringDate,
                         ytm: float,
                         convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the Macauley duration of the bond on a settlement date
        given its yield to maturity. '''

        dd = self.dollarDuration(settlementDate, ytm, convention)
        fp = self.fullPriceFromYTM(settlementDate, ytm, convention)
        md = dd * (1.0 + ytm / self._frequency) / fp
        return md

###############################################################################

    def modifiedDuration(self,
                         settlementDate: TuringDate,
                         ytm: float,
                         convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the modified duration of the bondon a settlement date
        given its yield to maturity. '''

        dd = self.dollarDuration(settlementDate, ytm, convention)
        fp = self.fullPriceFromYTM(settlementDate, ytm, convention)
        md = dd / fp
        return md

###############################################################################

    def convexityFromYTM(self,
                         settlementDate: TuringDate,
                         ytm: float,
                         convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the bond convexity from the yield to maturity. This
        function is vectorised with respect to the yield input. '''

        dy = 0.0001
        p0 = self.fullPriceFromYTM(settlementDate, ytm - dy, convention)
        p1 = self.fullPriceFromYTM(settlementDate, ytm, convention)
        p2 = self.fullPriceFromYTM(settlementDate, ytm + dy, convention)
        conv = ((p2 + p0) - 2.0 * p1) / dy / dy / p1 / self._par
        return conv

###############################################################################

    def cleanPriceFromYTM(self,
                          settlementDate: TuringDate,
                          ytm: float,
                          convention: TuringYTMCalcType = TuringYTMCalcType.UK_DMO):
        ''' Calculate the bond clean price from the yield to maturity. This
        function is vectorised with respect to the yield input. '''

        fullPrice = self.fullPriceFromYTM(settlementDate, ytm, convention)
        accruedAmount = self._accruedInterest * self._par / self._faceAmount
        cleanPrice = fullPrice - accruedAmount
        return cleanPrice

###############################################################################

    def cleanPriceFromDiscountCurve(self,
                                    settlementDate: TuringDate,
                                    discountCurve: TuringDiscountCurve):
        ''' Calculate the clean bond value using some discount curve to
        present-value the bond's cashflows back to the curve anchor date and
        not to the settlement date. '''

        self.calcAccruedInterest(settlementDate)
        fullPrice = self.fullPriceFromDiscountCurve(settlementDate,
                                                    discountCurve)

        accrued = self._accruedInterest * self._par / self._faceAmount
        cleanPrice = fullPrice - accrued
        return cleanPrice

##############################################################################

    def fullPriceFromDiscountCurve(self,
                                   settlementDate: TuringDate,
                                   discountCurve: TuringDiscountCurve):
        ''' Calculate the bond price using a provided discount curve to PV the
        bond's cashflows to the settlement date. As such it is effectively a
        forward bond price if the settlement date is after the valuation date.
        '''

        if settlementDate < discountCurve._valuationDate:
            raise TuringError("Bond settles before Discount curve date")

        if settlementDate > self._maturityDate:
            raise TuringError("Bond settles after it matures.")

        px = 0.0
        df = 1.0
        dfSettle = discountCurve.df(settlementDate)

        for dt in self._flowDates[1:]:

            # coupons paid on the settlement date are included            
            if dt >= settlementDate:
                df = discountCurve.df(dt)
                flow = self._coupon / self._frequency
                pv = flow * df
                px += pv

        px += df * self._redemption
        px = px / dfSettle

        return px * self._par

###############################################################################

    def currentYield(self, cleanPrice):
        ''' Calculate the current yield of the bond which is the
        coupon divided by the clean price (not the full price)'''

        y = self._coupon * self._par / cleanPrice
        return y

###############################################################################

    def yieldToMaturity(self,
                        settlementDate: TuringDate,
                        cleanPrice: float,
                        convention: TuringYTMCalcType = TuringYTMCalcType.US_TREASURY):
        ''' Calculate the bond's yield to maturity by solving the price
        yield relationship using a one-dimensional root solver. '''

        if type(cleanPrice) is float or type(cleanPrice) is np.float64:
            cleanPrices = np.array([cleanPrice])
        elif type(cleanPrice) is list or type(cleanPrice) is np.ndarray:
            cleanPrices = np.array(cleanPrice)
        else:
            raise TuringError("Unknown type for cleanPrice "
                              + str(type(cleanPrice)))

        self.calcAccruedInterest(settlementDate)
        accruedAmount = self._accruedInterest * self._par / self._faceAmount
        fullPrices = (cleanPrices + accruedAmount)
        ytms = []

        for fullPrice in fullPrices:

            argtuple = (self, settlementDate, fullPrice, convention)

            ytm = optimize.newton(_f,
                                  x0=0.05,  # guess initial value of 10%
                                  fprime=None,
                                  args=argtuple,
                                  tol=1e-8,
                                  maxiter=50,
                                  fprime2=None)

            ytms.append(ytm)

        if len(ytms) == 1:
            return ytms[0]
        else:
            return np.array(ytms)

###############################################################################

    def calcAccruedInterest(self,
                            settlementDate: TuringDate,
                            numExDividendDays: int = 0,
                            calendarType: TuringCalendarTypes = TuringCalendarTypes.WEEKEND):
        ''' Calculate the amount of coupon that has accrued between the
        previous coupon date and the settlement date. Note that for some day
        count schemes (such as 30E/360) this is not actually the number of days
        between the previous coupon payment date and settlement date. If the
        bond trades with ex-coupon dates then you need to supply the number of
        days before the coupon date the ex-coupon date is. You can specify the
        calendar to be used - NONE means only calendar days, WEEKEND is only 
        weekends or you can specify a country calendar for business days.'''

        numFlows = len(self._flowDates)

        if numFlows == 0:
            raise TuringError("Accrued interest - not enough flow dates.")

        for iFlow in range(1, numFlows):
            # coupons paid on a settlement date are paid 
            if self._flowDates[iFlow] >= settlementDate:
                self._pcd = self._flowDates[iFlow-1]
                self._ncd = self._flowDates[iFlow]
                break

        dc = TuringDayCount(self._accrualType)
        cal = TuringCalendar(calendarType)
        exDividendDate = cal.addBusinessDays(self._ncd, -numExDividendDays)

        (accFactor, num, _) = dc.yearFrac(self._pcd,
                                            settlementDate,
                                            self._ncd, 
                                            self._freqType)
        
        if settlementDate > exDividendDate:
            accFactor = accFactor - 1.0 / self._frequency

        self._alpha = 1.0 - accFactor * self._frequency
        self._accruedInterest = accFactor * self._faceAmount * self._coupon
        self._accruedDays = num
        
        return self._accruedInterest

###############################################################################

    def assetSwapSpread(
            self,
            settlementDate: TuringDate,
            cleanPrice: float,
            discountCurve: TuringDiscountCurve,
            swapFloatDayCountConventionType=TuringDayCountTypes.ACT_360,
            swapFloatFrequencyType=TuringFrequencyTypes.SEMI_ANNUAL,
            swapFloatCalendarType=TuringCalendarTypes.WEEKEND,
            swapFloatBusDayAdjustRuleType=TuringBusDayAdjustTypes.FOLLOWING,
            swapFloatDateGenRuleType=TuringDateGenRuleTypes.BACKWARD):
        ''' Calculate the par asset swap spread of the bond. The discount curve
        is a Ibor curve that is passed in. This function is vectorised with
        respect to the clean price. '''

        cleanPrice = np.array(cleanPrice)
        self.calcAccruedInterest(settlementDate)
        accruedAmount = self._accruedInterest * self._par / self._faceAmount
        bondPrice = cleanPrice + accruedAmount
        # Calculate the price of the bond discounted on the Ibor curve
        pvIbor = 0.0
        prevDate = self._pcd

        for dt in self._flowDates[1:]:
            
            # coupons paid on a settlement date are included
            if dt >= settlementDate:
                df = discountCurve.df(dt)
                pvIbor += df * self._coupon / self._frequency

        pvIbor += df * self._redemption

        # Calculate the PV01 of the floating leg of the asset swap
        # I assume here that the coupon starts accruing on the settlement date
        prevDate = self._pcd
        schedule = TuringSchedule(settlementDate,
                                  self._maturityDate,
                                  swapFloatFrequencyType,
                                  swapFloatCalendarType,
                                  swapFloatBusDayAdjustRuleType,
                                  swapFloatDateGenRuleType)

        dayCount = TuringDayCount(swapFloatDayCountConventionType)

        prevDate = self._pcd
        pv01 = 0.0
        for dt in schedule._adjustedDates[1:]:
            df = discountCurve.df(dt)
            yearFrac = dayCount.yearFrac(prevDate, dt)[0]
            pv01 = pv01 + yearFrac * df
            prevDate = dt

        asw = (pvIbor - bondPrice/self._par) / pv01
        return asw

###############################################################################

    def fullPriceFromOAS(self,
                         settlementDate: TuringDate,
                         discountCurve: TuringDiscountCurve,
                         oas: float):
        ''' Calculate the full price of the bond from its OAS given the bond
        settlement date, a discount curve and the oas as a number. '''

        self.calcAccruedInterest(settlementDate)
        f = self._frequency
        c = self._coupon

        pv = 0.0
        for dt in self._flowDates[1:]:
            
            # coupons paid on a settlement date are included
            if dt >= settlementDate:

                t = (dt - settlementDate) / gDaysInYear

                t = np.maximum(t, gSmall)

                df = discountCurve.df(dt)
                # determine the Ibor implied zero rate
                r = f * (np.power(df, -1.0 / t / f) - 1.0)
                # determine the OAS adjusted zero rate
                df_adjusted = np.power(1.0 + (r + oas)/f, -t * f)
                pv = pv + (c / f) * df_adjusted

        pv = pv + df_adjusted * self._redemption
        pv *= self._par
        return pv

###############################################################################

    def optionAdjustedSpread(self,
                             settlementDate: TuringDate,
                             cleanPrice: float,
                             discountCurve: TuringDiscountCurve):
        ''' Return OAS for bullet bond given settlement date, clean bond price
        and the discount relative to which the spread is to be computed. '''

        if type(cleanPrice) is float or type(cleanPrice) is np.float64:
            cleanPrices = np.array([cleanPrice])
        elif type(cleanPrice) is list or type(cleanPrice) is np.ndarray:
            cleanPrices = np.array(cleanPrice)
        else:
            raise TuringError("Unknown type for cleanPrice "
                              + str(type(cleanPrice)))

        self.calcAccruedInterest(settlementDate)

        accruedAmount = self._accruedInterest * self._par / self._faceAmount
        fullPrices = cleanPrices + accruedAmount

        oass = []

        for fullPrice in fullPrices:

            argtuple = (self, settlementDate, fullPrice, discountCurve)

            oas = optimize.newton(_g,
                                  x0=0.01,  # initial value of 1%
                                  fprime=None,
                                  args=argtuple,
                                  tol=1e-8,
                                  maxiter=50,
                                  fprime2=None)

            oass.append(oas)

        if len(oass) == 1:
            return oass[0]
        else:
            return np.array(oass)

###############################################################################

    def printFlows(self,
                   settlementDate: TuringDate):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''

        flow = self._faceAmount * self._coupon / self._frequency

        for dt in self._flowDates[1:-1]:
            # coupons paid on a settlement date are included
            if dt >= settlementDate:
                print("%12s" % dt, " %12.2f " % flow)

        redemptionAmount = self._faceAmount + flow
        print("%12s" % self._flowDates[-1], " %12.2f " % redemptionAmount)

###############################################################################

    def fullPriceFromSurvivalCurve(self,
                                   settlementDate: TuringDate,
                                   discountCurve: TuringDiscountCurve,
                                   survivalCurve: TuringDiscountCurve,
                                   recoveryRate: float):
        ''' Calculate discounted present value of flows assuming default model.
        The survival curve treats the coupons as zero recovery payments while
        the recovery fraction of the par amount is paid at default. For the 
        defaulting principal we discretise the time steps using the coupon
        payment times. A finer discretisation may handle the time value with
        more accuracy. I reduce any error by averaging period start and period
        end payment present values. ''' 

        f = self._frequency
        c = self._coupon

        pv = 0.0        
        prevQ = 1.0
        prevDf = 1.0

        defaultingPrincipalPVPayStart = 0.0
        defaultingPrincipalPVPayEnd = 0.0

        for dt in self._flowDates[1:]:
            
            # coupons paid on a settlement date are included
            if dt >= settlementDate:

                df = discountCurve.df(dt)
                q = survivalCurve.survProb(dt)

                # Add PV of coupon conditional on surviving to payment date  
                # Any default results in all subsequent coupons being lost
                # with zero recovery

                pv = pv + (c / f) * df * q
                dq = q - prevQ

                defaultingPrincipalPVPayStart += -dq * recoveryRate * prevDf
                defaultingPrincipalPVPayStart += -dq * recoveryRate * df

                # Add on PV of principal if default occurs in coupon period
                prevQ = q
                prevDf = df

        pv = pv + 0.50 * defaultingPrincipalPVPayStart
        pv = pv + 0.50 * defaultingPrincipalPVPayEnd
        pv = pv + df * q * self._redemption
        pv *= self._par
        return pv

###############################################################################

    def cleanPriceFromSurvivalCurve(self,
                                    settlementDate: TuringDate,
                                    discountCurve: TuringDiscountCurve,
                                    survivalCurve: TuringDiscountCurve,
                                    recoveryRate: float):
        ''' Calculate clean price value of flows assuming default model.
        The survival curve treats the coupons as zero recovery payments while
        the recovery fraction of the par amount is paid at default. ''' 

        self.calcAccruedInterest(settlementDate)

        fullPrice = self.fullPriceFromSurvivalCurve(settlementDate,
                                                    discountCurve,
                                                    survivalCurve,
                                                    recoveryRate)
        
        cleanPrice = fullPrice - self._accruedInterest
        return cleanPrice
    
###############################################################################

    def __repr__(self):
        
        s = labelToString("OBJECT TYPE", type(self).__name__)
        s += labelToString("ISSUE DATE", self._issueDate)
        s += labelToString("MATURITY DATE", self._maturityDate)
        s += labelToString("COUPON", self._coupon)
        s += labelToString("FREQUENCY", self._freqType)
        s += labelToString("ACCRUAL TYPE", self._accrualType)
        s += labelToString("FACE AMOUNT", self._faceAmount, "")
        return s

###############################################################################

    def _print(self):
        ''' Print a list of the unadjusted coupon payment dates used in
        analytic calculations for the bond. '''
        print(self)


###############################################################################