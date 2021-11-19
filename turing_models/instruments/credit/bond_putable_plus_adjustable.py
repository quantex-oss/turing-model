from dataclasses import dataclass, field
from typing import Union, List, Any

from turing_models.utilities.global_variables import gDaysInYear
from fundamental.turing_db.data import TuringDB
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequency, TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendar
from turing_models.instruments.credit.bond import Bond
from turing_models.instruments.credit.bond_fixed_rate import BondFixedRate

from turing_models.utilities.mathematics import testMonotonicity

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.market.curves.curve_adjust import CurveAdjust
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from enum import Enum
import numpy as np
from scipy import optimize


###############################################################################
# TODO: Make it possible to specify start and end of American Callable/Puttable
###############################################################################
# interp = TuringInterpTypes.FLAT_FWD_RATES.value

class TuringBondModelTypes(Enum):
    BLACK = 1
    HO_LEE = 2
    HULL_WHITE = 3
    BLACK_KARASINSKI = 4

###############################################################################


class TuringBondOptionTypes(Enum):
    EUROPEAN_CALL = 1
    EUROPEAN_PUT = 2
    AMERICAN_CALL = 3
    AMERICAN_PUT = 4


###############################################################################

class TuringYTMCalcType(Enum):
    UK_DMO = 1,
    US_STREET = 2,
    US_TREASURY = 3
    
###############################################################################

def _f(c, *args):
    ''' Function used to do root search in price to yield calculation. '''
    bond = args[0]
    price = args[1]
    bond.coupon = c
    px = bond.full_price_from_discount_curve()
    objFn = px - price
    return objFn


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondPutableAdjustable(Bond):
    """ Class for fixed coupon bonds with embedded put optionality and rights to adjust coupon on exercise date. """
    bond_type: str = None
    coupon: float = 0.0  # 票息
    curve_code: str = None  # 曲线编码
    ytm: float = None
    zero_dates: List[Any] = field(default_factory=list)  # 支持手动传入曲线（日期）
    zero_rates: List[Any] = field(default_factory=list)  # 支持手动传入曲线（利率）
    forward_dates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（日期）
    forward_rates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（利率）
    put_date: TuringDate = None
    put_price: float = 100.0
    adjust_bound_up: float = None
    adjust_bound_down: float = None
    _ytm: float = None
    _discount_curve = None
    _forward_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        
        if self.adjust_bound_up is not None:
            self._bound_up = self.coupon + self.adjust_bound_up
        else:
            self._bound_up = None
        if self.adjust_bound_down is not None:
            self._bound_down = self.coupon + self.adjust_bound_down
        else:
            self._bound_down = None
    
    @property
    def get_yield_curve(self):
        return TuringDB.bond_yield_curve(curve_code=self.curve_code, date=self.settlement_date_, df=False)[self.curve_code]
    
    @property
    def zero_dates_(self):
        return self.zero_dates or self.get_yield_curve['tenor']

    @property
    def zero_rates_(self):
        return self.zero_rates or self.get_yield_curve['spot_rate']
          
    @property
    def __ytm__(self):
        return self._ytm or self.ctx_ytm or self.ytm or self.yield_to_maturity()

    @__ytm__.setter
    def __ytm__(self, value: float):
        self._ytm = value

    def curve_adjust(self):
        """ 支持曲线旋转及平移 """
        ca = CurveAdjust(self.zero_dates,  # 曲线信息
                         self.zero_rates,
                         self.ctx_parallel_shift,  # 平移量（bps)
                         self.ctx_curve_shift,  # 旋转量（bps)
                         self.ctx_pivot_point,  # 旋转点（年）
                         self.ctx_tenor_start,  # 旋转起始（年）
                         self.ctx_tenor_end)  # 旋转终点（年）
        return ca.get_dates_result(), ca.get_rates_result()
             
    @property
    def zero_dates_adjusted(self):
        if self.ctx_parallel_shift or self.ctx_curve_shift or \
           self.ctx_pivot_point or self.ctx_tenor_start or \
           self.ctx_tenor_end:
            return self.curve_adjust()[0]
        else:
            return self.zero_dates_

    @property
    def zero_rates_adjusted(self):
        if self.ctx_parallel_shift or self.ctx_curve_shift or \
           self.ctx_pivot_point or self.ctx_tenor_start or \
           self.ctx_tenor_end:
            return self.curve_adjust()[1]
        else:
            return self.zero_rates_
        
    @property
    def dates(self):
        return self.settlement_date_.addYears(self.zero_dates_adjusted)
    
    @property
    def discount_curve(self):
        if self._discount_curve:
            return self._discount_curve
        return TuringDiscountCurveZeros(
            self.settlement_date_, self.dates, self.zero_rates_adjusted)

    @discount_curve.setter
    def discount_curve(self, value: Union[TuringDiscountCurveZeros, TuringDiscountCurveFlat]):
        self._discount_curve = value
        
    @property
    def forward_dates_(self):
        if self.forward_dates:
            return self.settlement_date_.addYears(self.forward_dates)
        else:
            forward_dates = self.dates.copy()
            forward_dates = list(filter(lambda x: x >= self.put_date, forward_dates))
            return forward_dates

    @property
    def forward_rates_(self):
        if self.forward_rates:
            return self.forward_rates
        else:
            curve_spot = self.discount_curve
            dc = TuringDayCount(self.accrual_type_)
            forward_rates = []
            for i in range(len(self.forward_dates_)):
                acc_factor = dc.yearFrac(self.settlement_date, self.forward_dates_[i])[0]
                if acc_factor == 0:
                    forward_rates.append(0)
                else:
                    dfIndex1 = curve_spot.df(self.settlement_date)
                    dfIndex2 = curve_spot.df(self.forward_dates_[i])
                    forward_rates.append((dfIndex1 / dfIndex2 - 1.0) / acc_factor)
            return forward_rates

    @property
    def discount_curve_flat(self):
        return TuringDiscountCurveFlat(self.settlement_date_,
                                       self.__ytm__)
    
    @property
    def forward_curve(self):
        if self._forward_curve:
            return self._forward_curve
        else:
            return TuringDiscountCurveZeros(
                  self.put_date, self.forward_dates_, self.forward_rates_,TuringFrequencyTypes.CONTINUOUS)

    @forward_curve.setter
    def forward_curve(self, value: Union[TuringDiscountCurveZeros, TuringDiscountCurveFlat]):
        self._forward = value

    @property
    def forward_curve_flat(self):
        return TuringDiscountCurveFlat(self.put_date,
                                       self.__ytm__)

    @property
    def clean_price_(self):
        return self.clean_price or self.clean_price_from_discount_curve()
        
            
   
 ###############################################################################
    # def full_price_from_discount_curve(self):
    #     ''' Calculate the bond price using a provided discount curve to PV the
    #     bond's cashflows to the settlement date. As such it is effectively a
    #     forward bond price if the settlement date is after the valuation date.
    #     '''
        
        # if settlementDate < discountCurve._valuationDate:
        #     raise TuringError("Bond settles before Discount curve date")

        # if settlementDate > self._maturityDate:
        #     raise TuringError("Bond settles after it matures.")

        # px = 0.0
        # df = 1.0
        # dfSettle = discountCurve.df(settlementDate)

        # for dt in self._flowDates[1:]:

        #     # coupons paid on the settlement date are included            
        #     if dt >= settlementDate:
        #         df = discountCurve.df(dt)
        #         flow = coupon / self._frequency
        #         pv = flow * df
        #         px += pv

        # px += df * self._redemption
        # px = px / dfSettle

        # return px * self._par

###############################################################################

    def _equilibrium_rate(self):
        ''' Calculate the equilibrium_rate by solving the price
        yield relationship using a one-dimensional root solver. '''
        
        dc = TuringDayCount(self.accrual_type_)
        forward_dates = []
        for i in range(len(self.forward_dates_)):
                forward_dates.append(dc.yearFrac(self.put_date, self.forward_dates_[i])[0])
        print(len(forward_dates))
        self._exercised_bond = BondFixedRate(value_date = self.put_date,
                                             issue_date = self.put_date,
                                             due_date = self.due_date,
                                             zero_dates = forward_dates,
                                             zero_rates = self.forward_rates_,
                                             freq_type = self.freq_type_,
                                             accrual_type = self.accrual_type_,
                                             par= self.par
                                             )
        
        clean_price = self.put_price
        if type(clean_price) is float or type(clean_price) is np.float64:
            clean_prices = np.array([clean_price])
        elif type(clean_price) is list or type(clean_price) is np.ndarray:
            clean_prices = np.array(clean_price)
        else:
            raise TuringError("Unknown type for cleanPrice "
                              + str(type(clean_price)))
        # self.calcAccruedInterest(settlementDate)
        accruedAmount = 0
        full_prices = (clean_prices + accruedAmount)
        equ_c = []

        for full_price in full_prices:

            argtuple = (self._exercised_bond, full_price)

            c = optimize.newton(_f,
                                  x0=0.05,  # guess initial value of 5%
                                  fprime=None,
                                  args=argtuple,
                                  tol=1e-8,
                                  maxiter=50,
                                  fprime2=None)

            equ_c.append(c)
        
        if len(equ_c) == 1:
            return equ_c[0]
        
        else:
            return np.array(equ_c)
        
    def dollar_convexity(self):
        return 0
    
    def dv01(self):
        return 0
###############################################################################       
    def full_price_from_discount_curve(self):
        ''' Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded. 
        The valuation is made according to the ZhongZheng recommendation. '''

        equ_c = self._equilibrium_rate()
        self._pure_bond = BondFixedRate(value_date = self.value_date,
                                        issue_date = self.issue_date,
                                        due_date = self.put_date,
                                        zero_dates = self.zero_dates_adjusted,
                                        zero_rates = self.zero_rates_adjusted,
                                        freq_type = self.freq_type_,
                                        accrual_type = self.accrual_type_,
                                        par= self.par
                                        )
        # direction and adjusted rate caluation:
        if self._bound_up is not None and self._bound_down is not None:
            if 0 < self.adjust_bound_down < self.adjust_bound_up:
                if equ_c > self._bound_up:
                    adjust_fix = self._bound_up
                    recommend_dir = "short"
                elif self._bound_down <= equ_c <= self._bound_up:
                    adjust_fix = equ_c
                    recommend_dir = "long"
                elif self.coupon < equ_c < self._bound_down:
                    adjust_fix = self.coupon
                    recommend_dir = "short"
                elif equ_c <= self.coupon:
                    adjust_fix = self.coupon
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs1!")
            elif self.adjust_bound_down < self.adjust_bound_up <= 0:
                if equ_c > self.coupon:
                    adjust_fix = self.coupon
                    recommend_dir = "short"
                elif self._bound_up < equ_c <= self.coupon:
                    adjust_fix = self._bound_up
                    recommend_dir = "short"
                elif self._bound_down <= equ_c <= self._bound_up:
                    adjust_fix = self.coupon
                    recommend_dir = "long"
                elif equ_c < self._bound_down:
                    adjust_fix = self._bound_down
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs2!")
            elif self.adjust_bound_down < 0 < self.adjust_bound_up:
                if equ_c >= self._bound_up:
                    adjust_fix = self._bound_up
                    recommend_dir = "short"
                elif self._bound_down < equ_c < self._bound_up:
                    adjust_fix = equ_c
                    recommend_dir = "long"
                elif equ_c <= self._bound_down:
                    adjust_fix = self._bound_down
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs3!")
            elif (self.adjust_bound_down == self.adjust_bound_up) and (self.adjust_bound_up != 0):
                if equ_c > max(self.coupon, self._bound_up):
                    adjust_fix = max(self.coupon, self._bound_up)
                    recommend_dir = "short"
                elif self.coupon < equ_c <= self._bound_down:
                    adjust_fix = self.coupon
                    recommend_dir = "short"
                elif self._bound_up < equ_c <= self.coupon:
                    adjust_fix = self._bound_up
                    recommend_dir = "short"
                elif equ_c <= min(self._bound_down, self.coupon):
                    adjust_fix = min(self._bound_down, self.coupon)
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound input4!")
        
        elif self._bound_up is None and (self._bound_down is not None):
            if equ_c >= self._bound_down:
                adjust_fix = equ_c
                recommend_dir = "long"
            elif self.coupon < equ_c <= self._bound_down:
                adjust_fix = self.coupon
                recommend_dir = "short"
            elif equ_c <= min(self.coupon, self._bound_down):
                adjust_fix = min(self.coupon, self._bound_down)
                recommend_dir = "long"
            else:
                raise TuringError("Check bound inputs5!")

        elif self._bound_up is not None and (self._bound_down is None):
            if equ_c >= max(self.coupon, self._bound_up):
                adjust_fix = max(self.coupon, self._bound_up)
                recommend_dir = "short"
            elif self._bound_up < equ_c <= self.coupon:
                adjust_fix = self._bound_up
                recommend_dir = "short"
            elif equ_c < self._bound_up:
                adjust_fix = equ_c
                recommend_dir = "long"
            else:
                raise TuringError("Check bound inputs6!")
        
        elif self._bound_up is None and (self._bound_down is None):
            adjust_fix = equ_c
            recommend_dir = "long"
        
        # Valuation:
        if recommend_dir == "long":
            # Generate bond coupon flow schedule
            cpn1 = self.coupon / self.frequency
            cpn2 = adjust_fix / self.frequency
            cpnTimes = []
            cpn_dates = []
            cpnAmounts = []

            for flow_date in self._flow_dates[1:]:
                if self.settlement_date_ < flow_date < self.put_date:
                    cpnTime = (flow_date - self.settlement_date_) / gDaysInYear
                    cpn_date = flow_date
                    cpnTimes.append(cpnTime)
                    cpn_dates.append(cpn_date)
                    cpnAmounts.append(cpn1)
                if flow_date >= self.put_date:
                    cpnTime = (flow_date - self.settlement_date) / gDaysInYear
                    cpn_date = flow_date
                    cpnTimes.append(cpnTime)
                    cpn_dates.append(cpn_date)
                    cpnAmounts.append(cpn2)
                    
            cpnTimes = np.array(cpnTimes)
            cpnAmounts = np.array(cpnAmounts)
            
            pv = 0
            dfSettle = self.discount_curve.df(self.settlement_date)
            numCoupons = len(cpnTimes)
            for i in range(0, numCoupons):
                # tcpn = cpnTimes[i]
                # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                df = self.discount_curve.df(cpn_dates[i])
                flow = cpnAmounts[i]
                pv += flow * df

            pv += df * self._redemption / dfSettle

            return pv * self.par

        elif recommend_dir == "short":
            v = self._pure_bond.full_price_from_discount_curve()
        return v

    def calc_accrued_interest(self):
        """ 应计利息 """

        num_flows = len(self._flow_dates)

        if num_flows == 0:
            raise TuringError("Accrued interest - not enough flow dates.")

        for i_flow in range(1, num_flows):
            if self._flow_dates[i_flow] >= self.settlement_date_:
                self._pcd = self._flow_dates[i_flow - 1]  # 结算日前一个现金流
                self._ncd = self._flow_dates[i_flow]  # 结算日后一个现金流
                break

        dc = TuringDayCount(self.accrual_type_)
        cal = TuringCalendar(self.calendar_type)
        ex_dividend_date = cal.addBusinessDays(
            self._ncd, -self.num_ex_dividend_days)  # 除息日

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self.settlement_date_,
                                           self._ncd,
                                           self.freq_type_)  # 计算应计日期，返回应计因数、应计天数、基数        

        if self.settlement_date_ > ex_dividend_date:  # 如果结算日大于除息日，减去一期
            acc_factor = acc_factor - 1.0 / self.frequency

        self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
        self._accrued_interest = acc_factor * self.par * self.coupon
        self._accrued_days = num

        return self._accrued_interest
    
    def clean_price_from_discount_curve(self):
        """ 通过利率曲线计算净价 """

        self.calc_accrued_interest()
        full_price = self.full_price_from_discount_curve()

        accrued = self._accrued_interest
        clean_price = full_price - accrued
        return clean_price
    
    def yield_to_maturity(self):
        """ 通过一维求根器计算YTM """

        clean_price = self.clean_price_
        if type(clean_price) is float \
                or type(clean_price) is int \
                or type(clean_price) is np.float64:
            clean_prices = np.array([clean_price])
        elif type(clean_price) is list \
                or type(clean_price) is np.ndarray:
            clean_prices = np.array(clean_price)
        else:
            raise TuringError("Unknown type for clean_price "
                              + str(type(clean_price)))

        self.calc_accrued_interest()
        accrued_amount = self._accrued_interest
        full_prices = (clean_prices + accrued_amount)
        ytms = []

        for full_price in full_prices:
            argtuple = (self, full_price)

            ytm = optimize.newton(_f,
                                  x0=0.05,  # guess initial value of 5%
                                  fprime=None,
                                  args=argtuple,
                                  tol=1e-8,
                                  maxiter=50,
                                  fprime2=None)

            ytms.append(ytm)
            self.ytm = None

        if len(ytms) == 1:
            return ytms[0]
        else:
            return np.array(ytms)


###############################################################################

    def __repr__(self):
        s = to_string("OBJECT TYPE", type(self).__name__)
        s += to_string("ISSUE DATE", self.issue_date)
        s += to_string("MATURITY DATE", self.due_date)
        s += to_string("COUPON", self.coupon)
        s += to_string("FREQUENCY", self.frequency)
        s += to_string("ACCRUAL TYPE", self.accrual_type_)
        s += to_string("FACE AMOUNT", self.par)

        # s += to_string("NUM CALL DATES", len(self._callDates))
        # for i in range(0, len(self._callDates)):
        #     s += "%12s %12.6f\n" % (self._callDates[i], self._callPrices[i])

        # s += to_string("NUM PUT DATES", len(self._putDate))
        # for i in range(0, len(self._putDate)):
        #     s += "%12s %12.6f\n" % (self._putDate[i], self._putPrice[i])

        return s

###############################################################################

    def _print(self):
        print(self)

###############################################################################
