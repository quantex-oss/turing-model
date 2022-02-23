import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import optimize

from turing_models.instruments.common import YieldCurve
from turing_models.instruments.rates.bond import Bond
from turing_models.instruments.rates.bond_fixed_rate import BondFixedRate
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.utilities.bond_terms import EcnomicTerms, EmbeddedPutableOptions, \
     EmbeddedRateAdjustmentOptions
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.utilities.helper_functions import datetime_to_turingdate, greek, newton_fun

dy = 0.0001


###############################################################################
# TODO: Make it possible to specify start and end of American Callable/Puttable
###############################################################################


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondPutableAdjustable(Bond):
    """ Class for fixed coupon bonds with embedded put optionality and rights to adjust coupon on exercise date. """
    ecnomic_terms: EcnomicTerms = None
    value_sys: str = "中债"

    def __post_init__(self):
        super().__post_init__()

    def _init(self):
        super()._init()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        self.dc = TuringDayCount(DayCountType.ACT_365F)
        self._bound_down = None
        self._bound_up = None
        self.fixed_rate_bond = None
        if self.issue_date:
            self.cv = YieldCurve(value_date=self.value_date, curve_code=self.curve_code)
            if self.curve_code is not None:
                self.cv.resolve()
                if self.cv.curve_data is not None:
                    self.discount_curve = self.cv.discount_curve()
        if self.ecnomic_terms is not None:
            self.check_ecnomic_terms()
            embedded_putable_options = self.ecnomic_terms.get_instance(EmbeddedPutableOptions)
            embedded_rate_adjustment_options = self.ecnomic_terms.get_instance(EmbeddedRateAdjustmentOptions)
            if embedded_putable_options is not None:
                embedded_putable_options_data = embedded_putable_options.data
                self.exercise_dates = datetime_to_turingdate(embedded_putable_options_data['exercise_date'].tolist())
                self.exercise_prices = embedded_putable_options_data['exercise_price'].tolist()
            if embedded_rate_adjustment_options is not None:
                embedded_rate_adjustment_options_data = embedded_rate_adjustment_options.data
                self.exercise_dates = datetime_to_turingdate(
                    embedded_rate_adjustment_options_data['exercise_date'].tolist())
                self.high_rate_adjust = embedded_rate_adjustment_options_data['high_rate_adjust'].tolist()
                self.low_rate_adjust = embedded_rate_adjustment_options_data['low_rate_adjust'].tolist()
            self.first_exe_info()

        if self.coupon_rate and self.fixed_rate_bond is None:
            if self.value_sys == "中债":
                if getattr(self, 'high_rate_adjust', None) and isinstance(self.high_rate_adjust, (float, int)):
                    self._bound_up = self.coupon_rate + self.high_rate_adjust
                else:
                    self._bound_up = None
                if getattr(self, 'low_rate_adjust', None) and isinstance(self.low_rate_adjust, (float, int)):
                    self._bound_down = self.coupon_rate + self.low_rate_adjust
                else:
                    self._bound_down = None

            elif self.value_sys == "中证":
                if getattr(self, 'high_rate_adjust', None) is None:
                    self.high_rate_adjust = float("inf")
                self._bound_up = self.coupon_rate + self.high_rate_adjust
                if getattr(self, 'low_rate_adjust', None) is None:
                    self.low_rate_adjust = float("-inf")
                self._bound_down = self.coupon_rate + self.low_rate_adjust

        if getattr(self, 'comb_symbol', None) is not None and getattr(self, 'exercise_dates', None) is not None and \
           getattr(self, 'due_date', None) is not None and getattr(self, 'pay_interest_cycle', None) is not None and \
           getattr(self, 'pay_interest_mode', None) is not None and getattr(self, 'interest_rules', None) is not None and \
           getattr(self, 'par', None) is not None and getattr(self, 'curve_code', None) and getattr(self, 'fixed_rate_bond', None) is None:
            self._exercised_bond = BondFixedRate(comb_symbol=self.comb_symbol,
                                                 value_date=self.exercise_dates,
                                                 issue_date=self.exercise_dates,
                                                 due_date=self.due_date,
                                                 pay_interest_cycle=self.pay_interest_cycle,
                                                 pay_interest_mode=self.pay_interest_mode,
                                                 interest_rules=self.interest_rules,
                                                 par=self.par)
        if getattr(self, 'settlement_date', None) is not None \
           and getattr(self, 'exercise_dates', None) is not None:
            # 提供给用户调用，用以通过what-if修改远期收益率曲线
            self.forward_term = self.dc.yearFrac(self.settlement_date, self.exercise_dates)[0]
            # 远期曲线目前支持两种生成方式：1、用户通过what-if传入；2、模型自己计算
            # 不需要调用接口获取，故不需要调用resolve
            self.forward_cv = YieldCurve(value_date=self.value_date,
                                         curve_code=self.curve_code,
                                         curve_type='forward_spot_rate',
                                         forward_term=self.forward_term)
        if getattr(self, 'discount_curve', None):
            self.compute_forward_rates()
            self.compute_forward_curve_data()
            self.compute_equilibrium_rate()
            self.recommend_dir, self.adjust_fix = self._recommend_dir()
            self.initialize_pure_bond()
            self._calc_accrued_interest()
            self._clean_price = self.clean_price_from_discount_curve()
            self._ytm = self.yield_to_maturity()

    def _adjust_data_based_on_ctx(self):
        super()._adjust_data_based_on_ctx()
        ctx_clean_price = self.ctx_clean_price
        ctx_ytm = self.ctx_ytm
        self.discount_curve = self.cv.discount_curve()
        self.forward_term = self.dc.yearFrac(self.settlement_date, self.exercise_dates)[0]
        self.forward_cv.set_value_date(self.value_date)
        # 查询用户是否通过what-if传入self.curve_code对应的远期的即期收益率曲线数据
        ctx_forward_curve = self.ctx_yield_curve(curve_type='forward_spot_rate',
                                                 forward_term=self.forward_term)
        self.forward_cv.set_curve_data(ctx_forward_curve)
        self.compute_forward_rates()
        self.compute_forward_curve_data()
        self.compute_equilibrium_rate()
        self.recommend_dir, self.adjust_fix = self._recommend_dir()
        self.initialize_pure_bond()
        self._calc_accrued_interest()
        self._clean_price = ctx_clean_price or self.clean_price_from_discount_curve()
        self._ytm = ctx_ytm or self.yield_to_maturity()

    def first_exe_info(self):
        if getattr(self, 'exercise_dates', None) and getattr(self, 'settlement_date', None):
            for i in range(len(self.exercise_dates)):
                if self.exercise_dates[i] > self.settlement_date:
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
            if isinstance(self.exercise_dates, list) and self.exercise_dates[-1] <= self.settlement_date:
                # No exercise info after valuation date. Treat as a fixed rate bond
                self.fixed_rate_bond = BondFixedRate(comb_symbol=self.comb_symbol,
                                                     value_date=self.settlement_date,
                                                     issue_date=self.exercise_dates[-1],
                                                     due_date=self.due_date,
                                                     coupon_rate=self.coupon_rate,
                                                     pay_interest_cycle=self.pay_interest_cycle,
                                                     pay_interest_mode=self.pay_interest_mode,
                                                     interest_rules=self.interest_rules,
                                                     par=self.par,
                                                     curve_code=self.curve_code)
                curve_dates = []
                _zero_dates = self.discount_curve._zeroDates
                for i in range(len(_zero_dates)):
                    curve_dates.append(self.dc.yearFrac(self.settlement_date, _zero_dates[i])[0])
                self.fixed_rate_bond.cv.set_curve_data(pd.DataFrame(data={'tenor': curve_dates, 'rate': _zero_dates}))

    @property
    def _forward_dates(self):
        forward_dates = self.discount_curve._zeroDates.copy()
        forward_dates = list(filter(lambda x: x >= self.exercise_dates, forward_dates))

        return forward_dates

    def compute_forward_rates(self):
        forward_dates = self._forward_dates
        curve_spot = self.discount_curve
        dfIndex1 = curve_spot.df(self.exercise_dates)
        forward_rates = []
        for i in range(len(forward_dates)):
            acc_factor = self.dc.yearFrac(self.exercise_dates, forward_dates[i])[0]
            if acc_factor == 0:
                forward_rates.append(0)
            else:
                dfIndex2 = curve_spot.df(forward_dates[i])
                forward_rates.append(math.pow(dfIndex1 / dfIndex2, 1 / acc_factor) - 1)
        self._forward_rates = forward_rates

    def compute_forward_curve_data(self):
        if getattr(self, 'forward_cv', None) is not None:
            if self.forward_cv.curve_data is None:
                forward_tenor = []
                for i in range(len(self._forward_dates)):
                    forward_tenor.append(self.dc.yearFrac(self.exercise_dates, self._forward_dates[i])[0])
                curve_data = pd.DataFrame(data={'tenor': forward_tenor, 'rate': self._forward_rates})
                self.forward_cv.set_curve_data(curve_data)
            self._forward_curve_data = self.forward_cv.curve_data

    def initialize_pure_bond(self):  # 假设行权日到期的债券
        if getattr(self, 'settlement_date', None):
            self._pure_bond = BondFixedRate(comb_symbol=self.comb_symbol,
                                            value_date=self.settlement_date,
                                            issue_date=self.issue_date,
                                            due_date=self.exercise_dates,
                                            coupon_rate=self.coupon_rate,
                                            pay_interest_mode=self.pay_interest_mode,
                                            pay_interest_cycle=self.pay_interest_cycle,
                                            interest_rules=self.interest_rules,
                                            par=self.par,
                                            curve_code=self.curve_code)
            curve_dates = []
            for i in range(len(self.discount_curve._zeroDates)):
                curve_dates.append(self.dc.yearFrac(self.settlement_date, self.discount_curve._zeroDates[i])[0])
            self._pure_bond.cv.curve_data = pd.DataFrame(data={'tenor': curve_dates, 'rate': self.discount_curve._zeroRates})
            return self._pure_bond

    def clean_price(self):
        # 定价接口调用
        return self._clean_price

    def full_price(self):
        # 定价接口调用
        return self._clean_price + self._accrued_interest

    def ytm(self):
        # 定价接口调用
        return self._ytm

    def compute_equilibrium_rate(self):
        """ Calculate the equilibrium_rate by solving the price
        yield relationship using a one-dimensional root solver. """
        if getattr(self, '_exercised_bond', None) is not None:
            self._exercised_bond.cv.set_curve_data(self._forward_curve_data)
            self._exercised_bond._clean_price = self.exercise_prices
            accruedAmount = 0
            full_price = (self._exercised_bond._clean_price + accruedAmount)
            argtuple = (self._exercised_bond, full_price, "coupon_rate", "full_price_from_discount_curve")

            c = optimize.newton(newton_fun,
                                x0=0.05,  # guess initial value of 5%
                                fprime=None,
                                args=argtuple,
                                tol=1e-8,
                                maxiter=50,
                                fprime2=None)

            self.equ_c = c

    def _recommend_dir(self):
        if getattr(self, 'equ_c', None) is not None:
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
        else:
            return None, None

    def full_price_from_ytm(self):
        """ Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded.
        The valuation is made according to the ZhongZheng recommendation. """

        # Valuation:
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.full_price_from_ytm()
        else:
            if self.recommend_dir == "long":
                # Generate bond coupon flow schedule
                cpn1 = self.coupon_rate / self.frequency
                cpn2 = self.adjust_fix / self.frequency
                cpnTimes = []
                cpn_dates = []
                cpnAmounts = []

                for flow_date in self._flow_dates[1:]:
                    if self.settlement_date <= flow_date < self.exercise_dates:
                        cpnTime = (flow_date - self.settlement_date) / gDaysInYear
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
                self.discount_curve_flat = TuringDiscountCurveFlat(
                    self.settlement_date,
                    self._ytm,
                    self.pay_interest_cycle,
                    self.interest_rules
                )
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
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.full_price_from_discount_curve()
        else:
            if self.recommend_dir is not None:
                if self.recommend_dir == "long":
                    # Generate bond coupon flow schedule
                    cpn1 = self.coupon_rate / self.frequency
                    cpn2 = self.adjust_fix / self.frequency
                    cpnTimes = []
                    cpn_dates = []
                    cpnAmounts = []

                    for flow_date in self._flow_dates[1:]:
                        if self.settlement_date <= flow_date < self.exercise_dates:
                            cpnTime = (flow_date - self.settlement_date) / gDaysInYear
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

    def _calc_accrued_interest(self):
        """ 应计利息 """
        if getattr(self, '_flow_dates', None) is not None:
            num_flows = len(self._flow_dates)

            if num_flows == 0:
                raise TuringError("Accrued interest - not enough flow dates.")

            for i_flow in range(1, num_flows):
                if self._flow_dates[i_flow] >= self.settlement_date:
                    self._pcd = self._flow_dates[i_flow - 1]  # 结算日前一个现金流
                    self._ncd = self._flow_dates[i_flow]  # 结算日后一个现金流
                    break

            dc = TuringDayCount(self.interest_rules)
            # cal = TuringCalendar(self.calendar_type)
            ex_dividend_date = self.calendar.addBusinessDays(
                self._ncd, -self.num_ex_dividend_days)  # 除息日

            (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                               self.settlement_date,
                                               self._ncd,
                                               self.pay_interest_cycle)  # 计算应计日期，返回应计因数、应计天数、基数

            if self.settlement_date > ex_dividend_date:  # 如果结算日大于除息日，减去一期
                acc_factor = acc_factor - 1.0 / self.frequency

            self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
            self._accrued_interest = acc_factor * self.par * self.coupon_rate
            self._accrued_days = num

    def clean_price_from_discount_curve(self):
        """ 通过利率曲线计算净价 """
        if getattr(self, '_accrued_interest', None) is not None:
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
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond._ytm
        else:
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
                    raise TuringError("Unknown type for market_clean_price: " + str(type(clean_price)))

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
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.dv01()
        else:
            if self.recommend_dir == "long":
                if not self.isvalid():
                    raise TuringError("Bond settles after it matures.")
                return greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy
            elif self.recommend_dir == "short":
                return self._pure_bond.dv01()

    def macauley_duration(self):
        """ 麦考利久期 """
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.macauley_duration()
        else:
            if self.recommend_dir == "long":
                cpn1 = self.coupon_rate / self.frequency
                cpn2 = self.adjust_fix / self.frequency
                cpnTimes = []
                cpn_dates = []
                cpnAmounts = []
                px = 0.0
                df = 1.0
                df_settle = self.discount_curve.df(self.settlement_date)
                dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

                for flow_date in self._flow_dates[1:]:
                    dates = dc.yearFrac(self.settlement_date, flow_date)[0]
                    if self.settlement_date <= flow_date < self.exercise_dates:
                        cpnTime = (flow_date - self.settlement_date) / gDaysInYear
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
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.modified_duration()
        else:
            dmac = self.macauley_duration()
            md = dmac / (1.0 + self._ytm / self.frequency)
            return md

    def dollar_convexity(self):
        """ 凸性 """
        if self.fixed_rate_bond is not None:
            return self.fixed_rate_bond.dollar_convexity()
        else:
            if self.recommend_dir == 'long':
                if not self.isvalid():
                    raise TuringError("Bond settles after it matures.")
                return greek(self, self.full_price_from_ytm, "_ytm", order=2)
            elif self.recommend_dir == "short":
                return self._pure_bond.dollar_convexity()

    def check_ecnomic_terms(self):
        """检测ecnomic_terms是否为字典格式，若为字典格式，则处理成EcnomicTerms的实例对象"""
        ecnomic_terms = getattr(self, 'ecnomic_terms', None)
        if ecnomic_terms is not None and isinstance(ecnomic_terms, dict):
            embedded_putable_options = EmbeddedPutableOptions(
                data=ecnomic_terms.get('embedded_putable_options')
            )
            embedded_rate_adjustment_options = EmbeddedRateAdjustmentOptions(
                data=ecnomic_terms.get('embedded_rate_adjustment_options')
            )
            ecnomic_terms = EcnomicTerms(
                embedded_putable_options,
                embedded_rate_adjustment_options
            )
            setattr(self, 'ecnomic_terms', ecnomic_terms)

    def _resolve(self):
        super()._resolve()
        # 对ecnomic_terms属性做单独处理
        self.check_ecnomic_terms()
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        if self.ecnomic_terms:
            s += f'''
{self.ecnomic_terms}'''
        return s
