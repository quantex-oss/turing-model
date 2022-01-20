import datetime
from dataclasses import dataclass, field
import math
from typing import Union, List, Any
# from fundamental.turing_db.data import TuringDB
from turing_models.utilities.bond_terms import EcnomicTerms, EmbeddedPutableOptions, \
     EmbeddedRateAdjustmentOptions, PrepaymentTerms
from turing_models.utilities.global_variables import gDaysInYear
from turing_models.instruments.common import newton_fun, YieldCurve, greek
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import FrequencyType
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.instruments.rates.bond import Bond
from turing_models.instruments.rates.bond_adv_redemption import BondAdvRedemption
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
class BondPutableAndRateAdjAndAdvRdp(Bond):
    """ Class for fixed coupon bonds with embedded put optionality and rights to adjust coupon on exercise date. """
    ecnomic_terms: EcnomicTerms = None
    value_sys: str = "中证"
    adv_rdp_bond: BondAdvRedemption = None
    __ytm: float = None
    __discount_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        self._bound_down = None
        self._bound_up = None
        self.dc = TuringDayCount(DayCountType.ACT_365F)
        if self.issue_date:
            self.cv = YieldCurve(value_date=self.settlement_date, curve_code=self.curve_code)
            if self.curve_code:
                self.cv.resolve()
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
            self.forward_init()
            prepayment_terms = self.ecnomic_terms.get_instance(PrepaymentTerms)
            if prepayment_terms is not None:
                prepayment_terms_data = prepayment_terms.data
                self.pay_dates = datetime_to_turingdate(prepayment_terms_data['pay_date'].tolist())
                cal = TuringCalendar(self.calendar_type)
                for i in range(len(self.pay_dates)):
                    self.pay_dates[i] = cal.adjust(self.pay_dates[i],TuringBusDayAdjustTypes.MODIFIED_FOLLOWING) 
                self.pay_rates = prepayment_terms_data['pay_rate'].tolist()
                if len(self.pay_dates) != len(self.pay_rates):
                    raise TuringError("redemption terms should match redemption percents.")
                if round(sum(self.pay_rates), 10) != 1:  # 防止因为数据精度问题导致求和不为1
                    raise TuringError("total redemption doesn't equal to 1.")
                self._calculate_rdp_pcp()
            if self.coupon_rate:
                self._calculate_flow_amounts()

        if self.coupon_rate and self.adv_rdp_bond is None:
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

    @property
    def _ytm(self):
        return self.__ytm or self.ctx_ytm or self.yield_to_maturity()

    @_ytm.setter
    def _ytm(self, value: float):
        self.__ytm = value

    @property
    def forward_term(self):
        # 提供给用户调用，用以通过what-if修改远期收益率曲线
        return self.dc.yearFrac(self._settlement_date, self.exercise_dates)[0]

    @property
    def _discount_curve(self):
        if self.__discount_curve:
            return self.__discount_curve
        self._curve_resolve()
        return self.cv.discount_curve()

    @_discount_curve.setter
    def _discount_curve(self, value: TuringDiscountCurve):
        self.__discount_curve = value

    def _forward_curve_resolve(self):
        # 为了实时响应what-if调整pricing date
        self.forward_cv.set_value_date(self._settlement_date)
        # 查询用户是否通过what-if传入self.curve_code对应的远期的即期收益率曲线数据
        ctx_forward_curve = self.ctx_yield_curve(curve_type='forward_spot_rate',
                                                 forward_term=self.forward_term)
        if ctx_forward_curve is not None:
            self.forward_cv.set_curve_data(ctx_forward_curve)
        # 不需要调用接口获取，故不需要调用resolve

    @property
    def _forward_dates(self):
        forward_dates = self._discount_curve._zeroDates.copy()
        forward_dates = list(filter(lambda x: x >= self.exercise_dates, forward_dates))

        return forward_dates

    @property
    def _forward_rates(self):
        forward_dates = self._forward_dates
        curve_spot = self._discount_curve
        dfIndex1 = curve_spot.df(self.exercise_dates)
        forward_rates = []
        for i in range(len(forward_dates)):
            acc_factor = self.dc.yearFrac(self.exercise_dates, forward_dates[i])[0]
            if acc_factor == 0:
                forward_rates.append(0)
            else:
                dfIndex2 = curve_spot.df(forward_dates[i])
                forward_rates.append(math.pow(dfIndex1 / dfIndex2, 1 / acc_factor) - 1)
        return forward_rates

    @property
    def discount_curve_flat(self):
        return TuringDiscountCurveFlat(self._settlement_date,
                                       self._ytm, self.pay_interest_cycle, self.interest_rules)

    @property
    def _forward_curve_data(self):
        self._forward_curve_resolve()
        if self.forward_cv.curve_data is None:
            forward_tenor = []
            for i in range(len(self._forward_dates)):
                forward_tenor.append(self.dc.yearFrac(self.exercise_dates, self._forward_dates[i])[0])
            curve_data = pd.DataFrame(data={'tenor': forward_tenor, 'rate': self._forward_rates})
            self.forward_cv.set_curve_data(curve_data)
        return self.forward_cv.curve_data

    @property
    def _forward_curve_flat(self):
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
    def _pure_bond(self):  # 假设行权日到期的债券
        pay_dates = self.pay_dates[1:self.pay_dates.index(self.exercise_dates)+1]
        pay_rates = self.pay_rates[0:self.pay_dates.index(self.exercise_dates)]
        pay_rates[-1] = 1 - sum(pay_rates[0: -1])
        data = pd.DataFrame(data={'pay_date': pay_dates, 'pay_rate': pay_rates})
        pure_term = PrepaymentTerms(data=data) 
        ecnomic_terms = EcnomicTerms(pure_term)  
        pure_bond = BondAdvRedemption(comb_symbol=self.comb_symbol,
                                  value_date=self._settlement_date,
                                  issue_date=self.issue_date,
                                  due_date=self.exercise_dates,
                                  coupon_rate=self.coupon_rate,
                                  pay_interest_mode=self.pay_interest_mode,
                                  pay_interest_cycle=self.pay_interest_cycle,
                                  interest_rules=self.interest_rules,
                                  par=self.par,
                                  curve_code=self.curve_code,
                                  ecnomic_terms=ecnomic_terms)
        curve_dates = []
        for i in range(len(self._discount_curve._zeroDates)):
            curve_dates.append(self.dc.yearFrac(self._settlement_date, self._discount_curve._zeroDates[i])[0])
        pure_bond.cv.curve_data = pd.DataFrame(data={'tenor': curve_dates, 'rate': self._discount_curve._zeroRates})
        return pure_bond
    
    def forward_init(self):
        if self.issue_date and self.due_date and not isinstance(self.exercise_dates, list):
            forward_term = self.dc.yearFrac(self._settlement_date, self.exercise_dates)
            # 远期曲线目前支持两种生成方式：1、用户通过what-if传入；2、模型自己计算
            # 不需要调用接口获取，故不需要调用resolve
            self.forward_cv = YieldCurve(value_date=self.settlement_date,
                                         curve_code=self.curve_code,
                                         curve_type='forward_spot_rate',
                                         forward_term=forward_term)
    
    def first_exe_info(self):
        if self.exercise_dates and getattr(self, '_settlement_date', None):
            for i in range(len(self.exercise_dates)):
                if self.exercise_dates[i] > self._settlement_date:
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
            if isinstance(self.exercise_dates, list) and self.exercise_dates[-1] <= self._settlement_date:
                print("No exercise info after valation date. Treat as an advance redemption bond")
                prepayment_terms = self.ecnomic_terms.get_instance(PrepaymentTerms)
                ecnomic_terms = EcnomicTerms(prepayment_terms)
                self.adv_rdp_bond = BondAdvRedemption(comb_symbol=self.comb_symbol,
                                                    value_date=self._settlement_date,
                                                    issue_date=self.exercise_dates[-1],
                                                    due_date=self.due_date,
                                                    coupon_rate=self.coupon_rate,
                                                    pay_interest_cycle=self.pay_interest_cycle,
                                                    pay_interest_mode=self.pay_interest_mode,
                                                    interest_rules=self.interest_rules,
                                                    par=self.par,
                                                    curve_code=self.curve_code,
                                                    ecnomic_terms=ecnomic_terms)
                curve_dates = []
                for i in range(len(self._discount_curve._zeroDates)):
                    curve_dates.append(self.dc.yearFrac(self._settlement_date, self._discount_curve._zeroDates[i])[0])
                self.adv_rdp_bond.cv.curve_data = pd.DataFrame(data={'tenor': curve_dates, 'rate': self._discount_curve._zeroRates})
    
    def _calculate_rdp_pcp(self):
        """ Determine the bond remaining principal."""

        self.pay_dates.insert(0, self.issue_date)
        self.remaining_principal = [1]
        for i in range(len(self.pay_dates) - 1):
            self.remaining_principal.append(self.remaining_principal[i] - self.pay_rates[i])
            
    def _calculate_flow_amounts(self):
        """ 保存票息现金流信息 """

        self._flow_amounts = [0.0]

        for _ in self._flow_dates[1:]:
            cpn = self.coupon_rate / self.frequency
            self._flow_amounts.append(cpn)

    def clean_price(self):
        # 定价接口调用
        return self._clean_price

    def full_price(self):
        # 定价接口调用
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self._clean_price + self.calc_accrued_interest()

    def ytm(self):
        # 定价接口调用
        return self._ytm

    def _equilibrium_rate(self):
        """ Calculate the equilibrium_rate by solving the price
        yield relationship using a one-dimensional root solver. """

        # pay_dates = self.pay_dates[self.pay_dates.index(self.exercise_dates) + 1:]
        pay_rates = self.pay_rates[self.pay_dates.index(self.exercise_dates):]
        face_remaining = self.par * sum(pay_rates)
        prepayment_terms = self.ecnomic_terms.get_instance(PrepaymentTerms)
        ecnomic_terms = EcnomicTerms(prepayment_terms)
        exercised_bond = BondAdvRedemption(comb_symbol=self.comb_symbol,
                                       value_date=self.exercise_dates,
                                       issue_date=self.issue_date,
                                       due_date=self.due_date,
                                       pay_interest_cycle=self.pay_interest_cycle,
                                       pay_interest_mode=self.pay_interest_mode,
                                       interest_rules=self.interest_rules,
                                       par=self.par,
                                       curve_code=self.curve_code,
                                       ecnomic_terms=ecnomic_terms)
        exercised_bond.cv.set_curve_data(self._forward_curve_data)
        exercised_bond._clean_price = face_remaining

        accruedAmount = 0
        full_price = (exercised_bond._clean_price + accruedAmount)
        argtuple = (exercised_bond, full_price, "coupon_rate", "full_price_from_discount_curve")

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
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.full_price_from_ytm()
        else:
            if self.recommend_dir == "long":
                # Generate bond coupon flow schedule
                df = 1.0
                for rdp in range(len(self.pay_dates)):
                    if self._settlement_date < self.pay_dates[rdp]:
                        break
                next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
                last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
                count = 0
                cpnTimes = []
                cpn_dates = []
                cpnAmounts = []

                for flow_date in self._flow_dates[1:]:        
                    if self._settlement_date <= flow_date < self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.coupon_rate / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0
            
                    if flow_date >= self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.adjust_fix / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.adjust_fix / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0
                        
                cpnTimes = np.array(cpnTimes)
                cpnAmounts = np.array(cpnAmounts)

                pv = 0
                df_settle = self.discount_curve_flat.df(self._settlement_date)
                num_coupons = len(cpnTimes)
                for i in range(0, num_coupons):
                    # tcpn = cpnTimes[i]
                    # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                    df = self.discount_curve_flat.df(cpn_dates[i])
                    flow = cpnAmounts[i]
                    pv += flow * df
                pv += df * last_pcp
                return pv * self.par / df_settle

            elif self.recommend_dir == "short":
                v = self._pure_bond.full_price_from_ytm()
            return v

    def full_price_from_discount_curve(self):
        ''' Value the bond that settles on the specified date, which have
        both an put option and an option to adjust the coupon rates embedded.
        The valuation is made according to the ZhongZheng recommendation. '''

        # Valuation:
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.full_price_from_discount_curve()
        else:
            if self.recommend_dir == "long":
                # Generate bond coupon flow schedule
                df = 1.0
                for rdp in range(len(self.pay_dates)):
                    if self._settlement_date < self.pay_dates[rdp]:
                        break
                next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
                last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
                count = 0
                cpnTimes = []
                cpn_dates = []
                cpnAmounts = []

                for flow_date in self._flow_dates[1:]:
                    if self._settlement_date <= flow_date < self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.coupon_rate / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0
                        
                    if flow_date >= self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.adjust_fix / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.adjust_fix / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0
                        
                cpnTimes = np.array(cpnTimes)
                cpnAmounts = np.array(cpnAmounts)

                pv = 0
                df_settle = self._discount_curve.df(self._settlement_date)
                num_coupons = len(cpnTimes)
                for i in range(0, num_coupons):
                    # tcpn = cpnTimes[i]
                    # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                    df = self._discount_curve.df(cpn_dates[i])
                    flow = cpnAmounts[i]
                    pv += flow * df
                pv += df * last_pcp

                return pv * self.par / df_settle

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
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond._ytm
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
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.dv01()
        else:
            if self.recommend_dir == "long":
                if not self.isvalid():
                    raise TuringError("Bond settles after it matures.")
                return greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy
            elif self.recommend_dir == "short":
                return self._pure_bond.dv01()

    def macauley_duration(self):
        """ 麦考利久期 """
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.macauley_duration()
        else:
            if self.recommend_dir == "long":
                cpnTimes = []
                cpn_dates = []
                cpnAmounts = []
                df = 1.0
                for rdp in range(len(self.pay_dates)):
                    if self._settlement_date < self.pay_dates[rdp]:
                        break
                next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
                last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
                count = 0
                dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

                for flow_date in self._flow_dates[1:]:
                    dates = dc.yearFrac(self._settlement_date, flow_date)[0]
                    if self._settlement_date <= flow_date < self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.coupon_rate / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0
                        
                    if flow_date >= self.exercise_dates:
                        cpnTime = (flow_date - self._settlement_date) / gDaysInYear
                        cpn_date = flow_date
                        cpnTimes.append(cpnTime)
                        cpn_dates.append(cpn_date)
                        if flow_date < next_rdp:
                            flow = self.adjust_fix / self.frequency * last_pcp
                            cpnAmounts.append(flow)                            
                        if flow_date == next_rdp:  # 当提前偿还发生时的现金流
                            flow = self.adjust_fix / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                            cpnAmounts.append(flow)
                            count += 1
                            next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                            last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0

                cpnTimes = np.array(cpnTimes)
                cpnAmounts = np.array(cpnAmounts)

                pv = 0
                df_settle = self._discount_curve.df(self._settlement_date)
                numCoupons = len(cpnTimes)
                for i in range(0, numCoupons):
                    # tcpn = cpnTimes[i]
                    # df_flow = _uinterpolate(tcpn, dfTimes, dfValues, interp)
                    df = self._discount_curve.df(cpn_dates[i])
                    flow = cpnAmounts[i]
                    pv += flow * df * dates * self.par
                pv += df * last_pcp * self.par * dates
                px = pv / df_settle
                fp = self.full_price_from_ytm()

                dmac = px / fp

                return dmac

            elif self.recommend_dir == "short":
                dmac = self._pure_bond.macauley_duration()

            return dmac

    def modified_duration(self):
        """ 修正久期 """
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.modified_duration()
        else:
            dmac = self.macauley_duration()
            md = dmac / (1.0 + self._ytm / self.frequency)
            return md

    def dollar_convexity(self):
        """ 凸性 """
        if self.adv_rdp_bond is not None:
            return self.adv_rdp_bond.dollar_convexity()
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
        separator: str = "\n"
        if self.ecnomic_terms:
            s += f"{separator}{self.ecnomic_terms}"
        return s
