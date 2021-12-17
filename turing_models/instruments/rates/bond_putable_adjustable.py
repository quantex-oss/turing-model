from dataclasses import dataclass, field
import math
from typing import Union, List, Any

from turing_models.utilities.global_variables import gDaysInYear
from fundamental.turing_db.data import TuringDB
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendar
from turing_models.instruments.rates.bond import Bond
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.instruments.common import YieldCurveCode, RiskMeasure

from fundamental.pricing_context import PricingContext

import pandas as pd
import numpy as np
from scipy import optimize

dy = 0.0001
###############################################################################
# TODO: Make it possible to specify start and end of American Callable/Puttable
###############################################################################

def _f(c, *args):
    ''' Function used to do root search in price to yield calculation. '''
    bond = args[0]
    price = args[1]
    bond.coupon = c
    px = bond.full_price_from_discount_curve()
    objFn = px - price
    return objFn


def _g(y, *args):
    """ Function used to do root search in price to yield calculation. """
    bond = args[0]
    price = args[1]
    bond.__ytm__ = y
    px = bond.full_price_from_ytm()
    obj_fn = px - price
    return obj_fn


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondPutableAdjustable(Bond):
    """ Class for fixed coupon bonds with embedded put optionality and rights to adjust coupon on exercise date. """
    bond_type: str = None
    coupon: float = 0.0  # 票息
    # ytm: float = None
    forward_dates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（日期）
    forward_rates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（利率）
    put_date: TuringDate = None
    put_price: float = 100.0
    adjust_bound_up: float = None
    adjust_bound_down: float = None
    value_sys: str = "中债"
    _ytm: float = None
    _discount_curve = None
    _forward_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        
        if self.value_sys == "中债":
            if self.adjust_bound_up is not None:
                self._bound_up = self.coupon + self.adjust_bound_up
            else:
                self._bound_up = None
            if self.adjust_bound_down is not None:
                self._bound_down = self.coupon + self.adjust_bound_down
            else:
                self._bound_down = None
    
        elif self.value_sys == "中证":
            if self.adjust_bound_up is None:
                self.adjust_bound_up = float("inf")
            self._bound_up = self.coupon + self.adjust_bound_up
            if self.adjust_bound_down is None:
                self.adjust_bound_down = float("-inf")
            self._bound_down = self.coupon + self.adjust_bound_down
    
    
    @property
    def __ytm__(self):
        return self._ytm or self.ctx_ytm or self.yield_to_maturity()

    @__ytm__.setter
    def __ytm__(self, value: float):
        self._ytm = value
    
    @property
    def discount_curve(self):
        if self._discount_curve:
            return self._discount_curve
        self.curve_resolve()
        return self.cv.discount_curve()

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurve):
        self._discount_curve = value
        
    @property
    def forward_dates_(self):
        if self.forward_dates:
            return self.put_date.addYears(self.forward_dates)
        else:
            forward_dates = self.discount_curve._zeroDates.copy()
            forward_dates = list(filter(lambda x: x >= self.put_date, forward_dates))
            return forward_dates

    @property
    def forward_rates_(self):
        if self.forward_rates:
            return self.forward_rates
        else:
            curve_spot = self.discount_curve
            dfIndex1 = curve_spot.df(self.put_date)
            dc = TuringDayCount(TuringDayCountTypes.ACT_365F)
            forward_rates = []
            for i in range(len(self.forward_dates_)):
                acc_factor = dc.yearFrac(self.put_date, self.forward_dates_[i])[0]
                if acc_factor == 0:
                    forward_rates.append(0)
                else:
                    dfIndex2 = curve_spot.df(self.forward_dates_[i])
                    forward_rates.append(math.pow(dfIndex1 / dfIndex2, 1/acc_factor) - 1)
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
                  self.put_date, self.forward_dates_, self.forward_rates_,TuringFrequencyTypes.ANNUAL)

    @forward_curve.setter
    def forward_curve(self, value: Union[TuringDiscountCurveZeros, TuringDiscountCurveFlat]):
        self._forward = value

    @property
    def forward_curve_flat(self):
        return TuringDiscountCurveFlat(self.put_date,
                                       self.__ytm__)

    @property
    def clean_price_(self):
        return self.ctx_clean_price or self.clean_price_from_discount_curve()
    
    @property
    def equ_c(self):
        return self._equilibrium_rate()
    
    @property
    def recommend_dir(self):
        (recommend_dir, _) = self._recommend_dir()
        return recommend_dir
    
    @property
    def adjust_fix(self):
        (_, adjust_fix) = self._recommend_dir()
        return adjust_fix
    
    @property
    def _pure_bond(self):
        pure_bond = BondFixedRate(bond_symbol = "purebond",
                                  value_date = self.value_date,
                                  issue_date = self.issue_date,
                                  due_date = self.put_date,
                                  coupon = self.coupon,
                                  cpn_type = self.cpn_type,
                                  freq_type = self.freq_type,
                                  accrual_type = self.accrual_type,
                                  par= self.par)
        curve_dates = []
        dc = TuringDayCount(TuringDayCountTypes.ACT_365F)
        for i in range(len(self.discount_curve._zeroDates)):
                curve_dates.append(dc.yearFrac(self.settlement_date_, self.discount_curve._zeroDates[i])[0])
        pure_bond.cv.curve_data = pd.DataFrame(data={'tenor': curve_dates, 'rate': self.discount_curve._zeroRates})
        return pure_bond
    
    def clean_price(self):
        # 定价接口调用
        return self.clean_price_

    def full_price(self):
        # 定价接口调用
        return self.full_price_from_discount_curve()
    
    def ytm(self):
        # 定价接口调用
        return self.__ytm__

   
###############################################################################

    def _equilibrium_rate(self):
        ''' Calculate the equilibrium_rate by solving the price
        yield relationship using a one-dimensional root solver. '''
        
        dc = TuringDayCount(TuringDayCountTypes.ACT_365F)
        forward_dates = []
        for i in range(len(self.forward_dates_)):
                forward_dates.append(dc.yearFrac(self.put_date, self.forward_dates_[i])[0])
        self._exercised_bond = BondFixedRate(bond_symbol = "exercisedbond",
                                             value_date = self.put_date,
                                             issue_date = self.put_date,
                                             due_date = self.due_date,
                                             freq_type = self.freq_type,
                                             cpn_type = self.cpn_type,
                                             accrual_type = self.accrual_type,
                                             par= self.par)
        forward_curve = pd.DataFrame(data={'tenor': forward_dates, 'rate': self.forward_rates_})
        scenario_extreme = PricingContext(bond_yield_curve=[{"bond_symbol": "exercisedbond", "value": forward_curve}],
                                                            clean_price=[{"bond_symbol": "exercisedbond", "value": self.put_price}])
        accruedAmount = 0
        with scenario_extreme:
            full_price = (self._exercised_bond.calc(RiskMeasure.CleanPrice) + accruedAmount)
            argtuple = (self._exercised_bond, full_price)

            c = optimize.newton(_f,
                                x0=0.05,  # guess initial value of 5%
                                fprime=None,
                                args=argtuple,
                                tol=1e-8,
                                maxiter=50,
                                fprime2=None)

            return c
            
        
    def _recommend_dir(self):
        if self.value_sys == "中债":
            # direction and adjusted rate caluation:
            if self._bound_up is not None and self._bound_down is not None:
                if 0 < self.adjust_bound_down < self.adjust_bound_up:
                    if self.equ_c > self._bound_up:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self._bound_down <= self.equ_c <= self._bound_up:
                        adjust_fix = self.equ_c
                        recommend_dir = "long"
                    elif self.coupon < self.equ_c < self._bound_down:
                        adjust_fix = self.coupon
                        recommend_dir = "short"
                    elif self.equ_c <= self.coupon:
                        adjust_fix = self.coupon
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound inputs1!")
                elif self.adjust_bound_down < self.adjust_bound_up <= 0:
                    if self.equ_c > self.coupon:
                        adjust_fix = self.coupon
                        recommend_dir = "short"
                    elif self._bound_up < self.equ_c <= self.coupon:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self._bound_down <= self.equ_c <= self._bound_up:
                        adjust_fix = self.coupon
                        recommend_dir = "long"
                    elif self.equ_c < self._bound_down:
                        adjust_fix = self._bound_down
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound inputs2!")
                elif self.adjust_bound_down < 0 < self.adjust_bound_up:
                    if self.equ_c >= self._bound_up:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self._bound_down < self.equ_c < self._bound_up:
                        adjust_fix = self.equ_c
                        recommend_dir = "long"
                    elif self.equ_c <= self._bound_down:
                        adjust_fix = self._bound_down
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound inputs3!")
                elif (self.adjust_bound_down == self.adjust_bound_up) and (self.adjust_bound_up != 0):
                    if self.equ_c > max(self.coupon, self._bound_up):
                        adjust_fix = max(self.coupon, self._bound_up)
                        recommend_dir = "short"
                    elif self.coupon < self.equ_c <= self._bound_down:
                        adjust_fix = self.coupon
                        recommend_dir = "short"
                    elif self._bound_up < self.equ_c <= self.coupon:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self.equ_c <= min(self._bound_down, self.coupon):
                        adjust_fix = min(self._bound_down, self.coupon)
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound input4!")
            
            elif self._bound_up is None and (self._bound_down is not None):
                if self.equ_c >= self._bound_down:
                    adjust_fix = self.equ_c
                    recommend_dir = "long"
                elif self.coupon < self.equ_c <= self._bound_down:
                    adjust_fix = self.coupon
                    recommend_dir = "short"
                elif self.equ_c <= min(self.coupon, self._bound_down):
                    adjust_fix = min(self.coupon, self._bound_down)
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs5!")

            elif self._bound_up is not None and (self._bound_down is None):
                if self.equ_c >= max(self.coupon, self._bound_up):
                    adjust_fix = max(self.coupon, self._bound_up)
                    recommend_dir = "short"
                elif self._bound_up < self.equ_c <= self.coupon:
                    adjust_fix = self._bound_up
                    recommend_dir = "short"
                elif self.equ_c < self._bound_up:
                    adjust_fix = self.equ_c
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs6!")
            
            elif self._bound_up is None and (self._bound_down is None):
                adjust_fix = self.equ_c
                recommend_dir = "long"
            
            return recommend_dir, adjust_fix
        
        elif self.value_sys == "中证":
            if self.equ_c > self._bound_up:
                adjust_fix = self._bound_up
                recommend_dir = "short"
            elif self._bound_down <= self.equ_c <= self._bound_up:
                adjust_fix = self.equ_c
                recommend_dir = "short"
            elif self.equ_c < self._bound_down:
                adjust_fix = self._bound_down
                recommend_dir = "long"
            else:
                raise TuringError("Check bound inputs!")
            
            return recommend_dir, adjust_fix
###############################################################################       
    def full_price_from_ytm(self):
        ''' Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded. 
        The valuation is made according to the ZhongZheng recommendation. '''    
        
        # Valuation:
        if self.recommend_dir == "long":
            # Generate bond coupon flow schedule
            cpn1 = self.coupon / self.frequency
            cpn2 = self.adjust_fix / self.frequency
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
            dfSettle = self.discount_curve_flat.df(self.settlement_date)
            numCoupons = len(cpnTimes)
            for i in range(0, numCoupons):
                # tcpn = cpnTimes[i]
                # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                df = self.discount_curve_flat.df(cpn_dates[i])
                flow = cpnAmounts[i]
                pv += flow * df

            pv += df * self._redemption / dfSettle

            return pv * self.par

        elif self.recommend_dir == "short":
            v = self._pure_bond.full_price_from_ytm()
        return v
    
    def full_price_from_discount_curve(self):
        ''' Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded. 
        The valuation is made according to the ZhongZheng recommendation. '''
  
        
        # Valuation:
        if self.recommend_dir == "long":
            # Generate bond coupon flow schedule
            cpn1 = self.coupon / self.frequency
            cpn2 = self.adjust_fix / self.frequency
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

        elif self.recommend_dir == "short":
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

        dc = TuringDayCount(self.accrual_type)
        cal = TuringCalendar(self.calendar_type)
        ex_dividend_date = cal.addBusinessDays(
            self._ncd, -self.num_ex_dividend_days)  # 除息日

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self.settlement_date_,
                                           self._ncd,
                                           self.freq_type)  # 计算应计日期，返回应计因数、应计天数、基数        

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
    
    def clean_price_from_ytm(self):
        """ 通过YTM计算净价 """
        full_price = self.full_price_from_ytm()
        accrued_amount = self._accrued_interest
        clean_price = full_price - accrued_amount
        return clean_price
    
    def yield_to_maturity(self):
        """ 通过一维求根器计算YTM """
        if self.recommend_dir == "long":
            clean_price = self.clean_price_
            if type(clean_price) is float \
                    or type(clean_price) is int \
                    or type(clean_price) is np.float64:
                clean_prices = np.array([clean_price])
            elif type(clean_price) is list \
                    or type(clean_price) is np.ndarray:
                clean_prices = np.array(clean_price)
            else:
                raise TuringError("Unknown type for market_clean_price "
                                + str(type(clean_price)))

            self.calc_accrued_interest()
            accrued_amount = self._accrued_interest
            full_prices = (clean_prices + accrued_amount)
            ytms = []

            for full_price in full_prices:
                argtuple = (self, full_price)

                ytm = optimize.newton(_g,
                                    x0=0.05,  # guess initial value of 5%
                                    fprime=None,
                                    args=argtuple,
                                    tol=1e-8,
                                    maxiter=50,
                                    fprime2=None)

                ytms.append(ytm)
                self.__ytm__ = None

            if len(ytms) == 1:
                return ytms[0]
            else:
                return np.array(ytms)
            
        elif self.recommend_dir == "short":
            return self._pure_bond.yield_to_maturity()
    
    def dv01(self):
        """ 数值法计算dv01 """
        if self.recommend_dir == "long":
            ytm = self.__ytm__
            self.__ytm__ = ytm - dy
            p0 = self.full_price_from_ytm()
            self.__ytm__ = ytm + dy
            p2 = self.full_price_from_ytm()
            self.__ytm__ = None
            dv = -(p2 - p0) / 2.0
            return dv       
        elif self.recommend_dir == "short":
            return self._pure_bond.dv01()
        

    def macauley_duration(self):
        """ 麦考利久期 """

        if self.recommend_dir == "long":
            cpn1 = self.coupon / self.frequency
            cpn2 = self.adjust_fix / self.frequency
            cpnTimes = []
            cpn_dates = []
            cpnAmounts = []
            px = 0.0
            df = 1.0
            df_settle = self.discount_curve.df(self.settlement_date_)
            dc = TuringDayCount(TuringDayCountTypes.ACT_ACT_ISDA)

            for flow_date in self._flow_dates[1:]:
                dates = dc.yearFrac(self.settlement_date_, flow_date)[0]
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
            numCoupons = len(cpnTimes)
            for i in range(0, numCoupons):
                # tcpn = cpnTimes[i]
                # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                df = self.discount_curve.df(cpn_dates[i])
                flow = cpnAmounts[i]
                pv += flow * df * dates * self.par

            pv += df * self._redemption * self.par * dates
            px = pv / df_settle 
            fp = self.full_price_from_ytm()

            dmac = px / fp

            return dmac
        
        elif self.recommend_dir == "short":
            dmac = self._pure_bond.macauley_duration()

        return dmac

    def modified_duration(self):
        """ 修正久期 """

        dmac = self.macauley_duration()
        md = dmac / (1.0 + self.__ytm__ / self.frequency)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        if self.recommend_dir == 'long':
            ytm = self.__ytm__
            self.__ytm__ = ytm - dy
            p0 = self.full_price_from_ytm()
            self.__ytm__ = ytm
            p1 = self.full_price_from_ytm()
            self.__ytm__ = ytm + dy
            p2 = self.full_price_from_ytm()
            self.__ytm__ = None
            dollar_conv = ((p2 + p0) - 2.0 * p1) / dy / dy
            return dollar_conv
        elif self.recommend_dir == "short":
            return self._pure_bond.dollar_convexity()
        

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
