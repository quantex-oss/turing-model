import datetime
from dataclasses import dataclass, field
import math
from typing import Union, List, Any
# from fundamental.turing_db.data import TuringDB
from turing_models.utilities.bond_terms import EcnomicTerms, EmbeddedPutableOptions, \
     EmbeddedRateAdjustmentOptions
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.instruments.common import newton_fun, Curve
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.calendar import TuringCalendar
from turing_models.instruments.rates.bond import Bond
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.helper_functions import datetime_to_turingdate
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.instruments.common import RiskMeasure

import pandas as pd
import numpy as np
from scipy import optimize

dy = 0.0001


###############################################################################
# TODO: Make it possible to specify start and end of American Callable/Puttable
###############################################################################


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondPutableAdjustable(Bond):
    """ Class for fixed coupon bonds with embedded put optionality and rights to adjust coupon on exercise date. """
    ecnomic_terms: EcnomicTerms = None
    forward_dates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（日期）
    forward_rates: List[Any] = field(default_factory=list)  # 支持手动传入远期曲线（利率）
    value_sys: str = "中证"
    __ytm: float = None
    __discount_curve = None
    __forward_curve = None

    def __new__(cls, *args, **kwargs):
        if kwargs.get("value_date") is None:
            kwargs['value_date'] = datetime.date.today()
        ecnomic_terms = kwargs.get("ecnomic_terms")
        if ecnomic_terms is not None:
            embedded_putable_options = ecnomic_terms.get_instance(EmbeddedPutableOptions)
            if embedded_putable_options is not None:
                exercise_dates = datetime_to_turingdate(embedded_putable_options.data['exercise_date'].tolist())
                value_date = datetime_to_turingdate(kwargs["value_date"])
                if exercise_dates[-1] > value_date:
                    return super().__new__(cls)
                else:
                    del kwargs['ecnomic_terms']
                    fixed_rete_bond = BondFixedRate(**kwargs)
                    return fixed_rete_bond

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        if self.ecnomic_terms is not None:
            embedded_putable_options = self.ecnomic_terms.get_instance(EmbeddedPutableOptions)
            embedded_rate_adjustment_options = self.ecnomic_terms.get_instance(EmbeddedRateAdjustmentOptions)
            if embedded_putable_options is not None:
                embedded_putable_options_data = embedded_putable_options.data
                self.exercise_dates = datetime_to_turingdate(embedded_putable_options_data['exercise_date'].tolist())
                self.exercise_prices = embedded_putable_options_data['exercise_price'].tolist()
            if embedded_rate_adjustment_options is not None:
                embedded_rate_adjustment_options_data = embedded_rate_adjustment_options.data
                self.exercise_dates = datetime_to_turingdate(embedded_rate_adjustment_options_data['exercise_date'].tolist())
                self.high_rate_adjust = embedded_rate_adjustment_options_data['high_rate_adjust'].tolist()
                self.low_rate_adjust = embedded_rate_adjustment_options_data['low_rate_adjust'].tolist()

        if self.issue_date and self.due_date:
            self.forward_cv = Curve(value_date=self.settlement_date,
                                    curve_code=self.curve_code,
                                    curve_type='forward_spot_rate',
                                    forward_term=self.time_to_maturity_in_year)

        for i in range(len(self.exercise_dates)):
            if self.exercise_dates[i] > self.value_date:
                self.exercise_dates = self.exercise_dates[i]
                self.exercise_prices = self.exercise_prices[i]
                if len(self.high_rate_adjust) > 0:
                    self.high_rate_adjust = self.high_rate_adjust[i]
                else:
                    self.high_rate_adjust = None
                if len(self.low_rate_adjust) > 0:
                    self.low_rate_adjust = self.low_rate_adjust[i]
                else:
                    self.low_rate_adjust = None
                break

        if self.value_sys == "中债":
            if self.high_rate_adjust is not None:
                self._bound_up = self.coupon_rate + self.high_rate_adjust
            else:
                self._bound_up = None
            if self.low_rate_adjust is not None:
                self._bound_down = self.coupon_rate + self.low_rate_adjust
            else:
                self._bound_down = None

        elif self.value_sys == "中证":
            if self.high_rate_adjust is None:
                self.high_rate_adjust = float("inf")
            self._bound_up = self.coupon_rate + self.high_rate_adjust
            if self.low_rate_adjust is None:
                self.low_rate_adjust = float("-inf")
            self._bound_down = self.coupon_rate + self.low_rate_adjust

    @property
    def _ytm(self):
        return self.__ytm or self.ctx_ytm or self.yield_to_maturity()

    @_ytm.setter
    def _ytm(self, value: float):
        self.__ytm = value

    @property
    def discount_curve(self):
        if self.__discount_curve:
            return self.__discount_curve
        self._curve_resolve()
        return self.cv.discount_curve()

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurve):
        self.__discount_curve = value

    @property
    def _forward_dates(self):
        ctx_yield_curve = self.ctx_yield_curve(curve_type='forward_spot_rate',
                                               forward_term=self.time_to_maturity_in_year)
        if self.forward_dates:
            return self.exercise_dates.addYears(self.forward_dates)
        else:
            forward_dates = self.discount_curve._zeroDates.copy()
            forward_dates = list(filter(lambda x: x >= self.exercise_dates, forward_dates))
            return forward_dates

    @property
    def _forward_rates(self):
        if self.forward_rates:
            return self.forward_rates
        else:
            curve_spot = self.discount_curve
            dfIndex1 = curve_spot.df(self.exercise_dates)
            dc = TuringDayCount(DayCountType.ACT_365F)
            forward_rates = []
            for i in range(len(self._forward_dates)):
                acc_factor = dc.yearFrac(self.exercise_dates, self._forward_dates[i])[0]
                if acc_factor == 0:
                    forward_rates.append(0)
                else:
                    dfIndex2 = curve_spot.df(self._forward_dates[i])
                    forward_rates.append(math.pow(dfIndex1 / dfIndex2, 1 / acc_factor) - 1)
            return forward_rates

    @property
    def discount_curve_flat(self):
        return TuringDiscountCurveFlat(self._settlement_date,
                                       self._ytm, self.pay_interest_cycle, self.interest_rules)

    @property
    def forward_curve(self):
        if self.__forward_curve:
            return self.__forward_curve
        else:
            return TuringDiscountCurveZeros(
                self.exercise_dates, self._forward_dates, self._forward_rates, FrequencyType.ANNUAL)

    @forward_curve.setter
    def forward_curve(self, value: Union[TuringDiscountCurveZeros, TuringDiscountCurveFlat]):
        self.__forward_curve = value

    @property
    def forward_curve_flat(self):
        return TuringDiscountCurveFlat(self.exercise_dates,
                                       self._ytm)

    @property
    def _clean_price(self):
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
        pure_bond = BondFixedRate(comb_symbol=self.comb_symbol,
                                  value_date=self.value_date,
                                  issue_date=self.issue_date,
                                  due_date=self.exercise_dates,
                                  coupon_rate=self.coupon_rate,
                                  pay_interest_mode=self.pay_interest_mode,
                                  pay_interest_cycle=self.pay_interest_cycle,
                                  interest_rules=self.interest_rules,
                                  par=self.par)
        curve_dates = []
        dc = TuringDayCount(DayCountType.ACT_365F)
        for i in range(len(self.discount_curve._zeroDates)):
            curve_dates.append(dc.yearFrac(self._settlement_date, self.discount_curve._zeroDates[i])[0])
        pure_bond.cv.curve_data = pd.DataFrame(data={'tenor': curve_dates, 'rate': self.discount_curve._zeroRates})
        return pure_bond

    def clean_price(self):
        # 定价接口调用
        return self._clean_price

    def full_price(self):
        # 定价接口调用
        return self.full_price_from_discount_curve()

    def ytm(self):
        # 定价接口调用
        return self._ytm

    def _equilibrium_rate(self):
        """ Calculate the equilibrium_rate by solving the price
        yield relationship using a one-dimensional root solver. """

        dc = TuringDayCount(DayCountType.ACT_365F)
        forward_dates = []
        for i in range(len(self._forward_dates)):
            forward_dates.append(dc.yearFrac(self.exercise_dates, self._forward_dates[i])[0])
        self._exercised_bond = BondFixedRate(comb_symbol="exercisedbond",
                                             value_date=self.exercise_dates,
                                             issue_date=self.exercise_dates,
                                             due_date=self.due_date,
                                             pay_interest_cycle=self.pay_interest_cycle,
                                             pay_interest_mode=self.pay_interest_mode,
                                             interest_rules=self.interest_rules,
                                             par=self.par)
        forward_curve = pd.DataFrame(data={'tenor': forward_dates, 'rate': self._forward_rates})
        self._exercised_bond.cv.curve_data = forward_curve
        self._exercised_bond._clean_price = self.exercise_prices
        
        accruedAmount = 0
        full_price = (self._exercised_bond.calc(RiskMeasure.CleanPrice) + accruedAmount)
        argtuple = (self._exercised_bond, full_price, "coupon_rate", "full_price_from_discount_curve")

        c = optimize.newton(newton_fun,
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
                if 0 < self.low_rate_adjust < self.high_rate_adjust:
                    if self.equ_c > self._bound_up:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self._bound_down <= self.equ_c <= self._bound_up:
                        adjust_fix = self.equ_c
                        recommend_dir = "long"
                    elif self.coupon_rate < self.equ_c < self._bound_down:
                        adjust_fix = self.coupon_rate
                        recommend_dir = "short"
                    elif self.equ_c <= self.coupon_rate:
                        adjust_fix = self.coupon_rate
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound inputs1!")
                elif self.low_rate_adjust < self.high_rate_adjust <= 0:
                    if self.equ_c > self.coupon_rate:
                        adjust_fix = self.coupon_rate
                        recommend_dir = "short"
                    elif self._bound_up < self.equ_c <= self.coupon_rate:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self._bound_down <= self.equ_c <= self._bound_up:
                        adjust_fix = self.coupon_rate
                        recommend_dir = "long"
                    elif self.equ_c < self._bound_down:
                        adjust_fix = self._bound_down
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound inputs2!")
                elif self.low_rate_adjust < 0 < self.high_rate_adjust:
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
                elif (self.low_rate_adjust == self.high_rate_adjust) and (self.high_rate_adjust != 0):
                    if self.equ_c > max(self.coupon_rate, self._bound_up):
                        adjust_fix = max(self.coupon_rate, self._bound_up)
                        recommend_dir = "short"
                    elif self.coupon_rate < self.equ_c <= self._bound_down:
                        adjust_fix = self.coupon_rate
                        recommend_dir = "short"
                    elif self._bound_up < self.equ_c <= self.coupon_rate:
                        adjust_fix = self._bound_up
                        recommend_dir = "short"
                    elif self.equ_c <= min(self._bound_down, self.coupon_rate):
                        adjust_fix = min(self._bound_down, self.coupon_rate)
                        recommend_dir = "long"
                    else:
                        raise TuringError("Check bound input4!")

            elif self._bound_up is None and (self._bound_down is not None):
                if self.equ_c >= self._bound_down:
                    adjust_fix = self.equ_c
                    recommend_dir = "long"
                elif self.coupon_rate < self.equ_c <= self._bound_down:
                    adjust_fix = self.coupon_rate
                    recommend_dir = "short"
                elif self.equ_c <= min(self.coupon_rate, self._bound_down):
                    adjust_fix = min(self.coupon_rate, self._bound_down)
                    recommend_dir = "long"
                else:
                    raise TuringError("Check bound inputs5!")

            elif self._bound_up is not None and (self._bound_down is None):
                if self.equ_c >= max(self.coupon_rate, self._bound_up):
                    adjust_fix = max(self.coupon_rate, self._bound_up)
                    recommend_dir = "short"
                elif self._bound_up < self.equ_c <= self.coupon_rate:
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

    def full_price_from_ytm(self):
        """ Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded.
        The valuation is made according to the ZhongZheng recommendation. """

        # Valuation:
        if self.recommend_dir == "long":
            # Generate bond coupon flow schedule
            cpn1 = self.coupon_rate / self.frequency
            cpn2 = self.adjust_fix / self.frequency
            cpnTimes = []
            cpn_dates = []
            cpnAmounts = []

            for flow_date in self._flow_dates[1:]:
                if self._settlement_date < flow_date < self.exercise_dates:
                    cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                    cpn_date = flow_date
                    cpnTimes.append(cpnTime)
                    cpn_dates.append(cpn_date)
                    cpnAmounts.append(cpn1)
                if flow_date >= self.exercise_dates:
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
            cpn1 = self.coupon_rate / self.frequency
            cpn2 = self.adjust_fix / self.frequency
            cpnTimes = []
            cpn_dates = []
            cpnAmounts = []

            for flow_date in self._flow_dates[1:]:
                if self._settlement_date < flow_date < self.exercise_dates:
                    cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                    cpn_date = flow_date
                    cpnTimes.append(cpnTime)
                    cpn_dates.append(cpn_date)
                    cpnAmounts.append(cpn1)
                if flow_date >= self.exercise_dates:
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
            if self._flow_dates[i_flow] >= self._settlement_date:
                self._pcd = self._flow_dates[i_flow - 1]  # 结算日前一个现金流
                self._ncd = self._flow_dates[i_flow]  # 结算日后一个现金流
                break

        dc = TuringDayCount(self.interest_rules)
        cal = TuringCalendar(self.calendar_type)
        ex_dividend_date = cal.addBusinessDays(
            self._ncd, -self.num_ex_dividend_days)  # 除息日

        (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                           self._settlement_date,
                                           self._ncd,
                                           self.pay_interest_cycle)  # 计算应计日期，返回应计因数、应计天数、基数

        if self._settlement_date > ex_dividend_date:  # 如果结算日大于除息日，减去一期
            acc_factor = acc_factor - 1.0 / self.frequency

        self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
        self._accrued_interest = acc_factor * self.par * self.coupon_rate
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
            clean_price = self._clean_price
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
                argtuple = (self, full_price, "_ytm", "full_price_from_ytm")

                ytm = optimize.newton(newton_fun,
                                      x0=0.05,  # guess initial value of 5%
                                      fprime=None,
                                      args=argtuple,
                                      tol=1e-8,
                                      maxiter=50,
                                      fprime2=None)

                ytms.append(ytm)
                self._ytm = None

            if len(ytms) == 1:
                return ytms[0]
            else:
                return np.array(ytms)

        elif self.recommend_dir == "short":
            return self._pure_bond.yield_to_maturity()

    def dv01(self):
        """ 数值法计算dv01 """
        if self.recommend_dir == "long":
            ytm = self._ytm
            self._ytm = ytm - dy
            p0 = self.full_price_from_ytm()
            self._ytm = ytm + dy
            p2 = self.full_price_from_ytm()
            self._ytm = None
            dv = -(p2 - p0) / 2.0
            return dv
        elif self.recommend_dir == "short":
            return self._pure_bond.dv01()

    def macauley_duration(self):
        """ 麦考利久期 """

        if self.recommend_dir == "long":
            cpn1 = self.coupon_rate / self.frequency
            cpn2 = self.adjust_fix / self.frequency
            cpnTimes = []
            cpn_dates = []
            cpnAmounts = []
            px = 0.0
            df = 1.0
            df_settle = self.discount_curve.df(self._settlement_date)
            dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

            for flow_date in self._flow_dates[1:]:
                dates = dc.yearFrac(self._settlement_date, flow_date)[0]
                if self._settlement_date < flow_date < self.exercise_dates:
                    cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                    cpn_date = flow_date
                    cpnTimes.append(cpnTime)
                    cpn_dates.append(cpn_date)
                    cpnAmounts.append(cpn1)
                if flow_date >= self.exercise_dates:
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
        md = dmac / (1.0 + self._ytm / self.frequency)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        if self.recommend_dir == 'long':
            ytm = self._ytm
            self._ytm = ytm - dy
            p0 = self.full_price_from_ytm()
            self._ytm = ytm
            p1 = self.full_price_from_ytm()
            self._ytm = ytm + dy
            p2 = self.full_price_from_ytm()
            self._ytm = None
            dollar_conv = ((p2 + p0) - 2.0 * p1) / dy / dy
            return dollar_conv
        elif self.recommend_dir == "short":
            return self._pure_bond.dollar_convexity()

    def __repr__(self):
        s = super().__repr__()
        separator: str = "\n"
        if self.ecnomic_terms:
            s += f"{separator}{self.ecnomic_terms}"
        return s
