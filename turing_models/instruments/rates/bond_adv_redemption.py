from dataclasses import dataclass

import numpy as np
from scipy import optimize

from turing_models.instruments.common import newton_fun, greek, YieldCurve
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.bond_terms import EcnomicTerms, PrepaymentTerms
from turing_models.utilities.calendar import TuringCalendar, TuringBusDayAdjustTypes
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.helper_functions import datetime_to_turingdate
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondAdvRedemption(Bond):
    ecnomic_terms: EcnomicTerms = None
    __clean_price: float = None
    __ytm: float = None
    __discount_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        if self.issue_date:
            self.cv = YieldCurve(value_date=self.value_date, curve_code=self.curve_code)
        if self.ecnomic_terms is not None:
            self.check_ecnomic_terms()
            prepayment_terms = self.ecnomic_terms.get_instance(PrepaymentTerms)
            if prepayment_terms is not None:
                prepayment_terms_data = prepayment_terms.data
                self.pay_dates = datetime_to_turingdate(prepayment_terms_data['pay_date'].tolist())
                # cal = TuringCalendar(self.calendar_type)
                for i in range(len(self.pay_dates)):
                    self.pay_dates[i] = self.calendar.adjust(self.pay_dates[i], self.bus_day_adjust_type)
                self.pay_rates = prepayment_terms_data['pay_rate'].tolist()
                if len(self.pay_dates) != len(self.pay_rates):
                    raise TuringError("redemption terms should match redemption percents.")
                if round(sum(self.pay_rates), 10) != 1:  # 防止因为数据精度问题导致求和不为1
                    raise TuringError("total redemption doesn't equal to 1.")
                self._calculate_rdp_pcp()
        if self.coupon_rate:
            self._calculate_flow_amounts()
            
    @property
    def _ytm(self):
        return self.__ytm or self.ctx_ytm or self.yield_to_maturity()

    @_ytm.setter
    def _ytm(self, value: float):
        self.__ytm = value

    def ytm(self):
        # 定价接口调用
        return self._ytm

    def full_price(self):
        # 定价接口调用
        return self._clean_price + self.calc_accrued_interest()

    def clean_price(self):
        # 定价接口调用
        return self._clean_price

    def _calculate_rdp_pcp(self):
        """ Determine the bond remaining principal."""

        self.pay_dates.insert(0, self.issue_date)
        self.remaining_principal = [1]
        for i in range(len(self.pay_dates) - 1):
            self.remaining_principal.append(self.remaining_principal[i] - self.pay_rates[i])
        
    @property
    def _discount_curve(self):
        if self.__discount_curve:
            return self.__discount_curve
        self._curve_resolve()
        return self.cv.discount_curve()
    
    @_discount_curve.setter
    def _discount_curve(self, value: TuringDiscountCurve):
        self.__discount_curve = value

    @property
    def _clean_price(self):
        return self.__clean_price or self.ctx_clean_price or self.clean_price_from_discount_curve()
    
    @_clean_price.setter
    def _clean_price(self, value: float):
        self.__clean_price = value

    def _calculate_flow_amounts(self):
        """ 保存票息现金流信息 """

        self._flow_amounts = [0.0]

        for _ in self._flow_dates[1:]:
            cpn = self.coupon_rate / self.frequency
            self._flow_amounts.append(cpn)

    def dv01(self):
        """ 数值法计算dv01 """
        return greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy

    def macauley_duration(self):
        """ 麦考利久期 """
        discount_curve_flat = TuringDiscountCurveFlat(
            self.settlement_date,
            self._ytm,
            self.pay_interest_cycle,
            self.interest_rules
        )

        px = 0.0
        df = 1.0
        df_settle = discount_curve_flat.df(self.settlement_date)
        for rdp in range(len(self.pay_dates)):  # 用rdp记录估值日后第一个偿还日在条款中的位置
            if self.settlement_date < self.pay_dates[rdp]:
                break
        next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0
        dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

        for dt in self._flow_dates[1:]:
            dates = dc.yearFrac(self.settlement_date, dt)[0]
            if dt >= self.settlement_date:  # 将结算日的票息加入计算
                df = discount_curve_flat.df(dt)
                if dt < next_rdp:
                    flow = self.coupon_rate / self.frequency * last_pcp
                    pv = flow * df * self.par * dates
                    px += pv
                if dt == next_rdp:  # 计算当提前偿还发生时的现金流，通过count向后迭代提前偿还条款信息和计算剩余本金
                    flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                    count += 1
                    pv = flow * df * dates * self.par
                    px += pv
                    next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0

        px += df * last_pcp * self.par * dates
        px = px / df_settle

        self._discount_curve = discount_curve_flat
        fp = self.full_price_from_discount_curve()
        self._discount_curve = None

        dmac = px / fp

        return dmac

    def modified_duration(self):
        """ 修正久期 """

        dmac = self.macauley_duration()
        md = dmac / (1.0 + self._ytm / self.frequency)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        return greek(self, self.full_price_from_ytm, "_ytm", order=2)

    def full_price_from_ytm(self):
        """ 通过YTM计算全价 """
        self.calc_accrued_interest()

        ytm = np.array(self._ytm)  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0

        if self.settlement_date > self.due_date:
            raise TuringError("Bond settles after it matures.")
        
        discount_curve_flat = TuringDiscountCurveFlat(
            self.settlement_date,
            self._ytm,
            self.pay_interest_cycle,
            self.interest_rules
        )

        px = 0.0
        df = 1.0
        df_settle = discount_curve_flat.df(self.settlement_date)
        for rdp in range(len(self.pay_dates)):
            if self.settlement_date < self.pay_dates[rdp]:
                break
        next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0

        for dt in self._flow_dates[1:]:

            if dt >= self.settlement_date:  # 将结算日的票息加入计算
                df = discount_curve_flat.df(dt)
                if dt < next_rdp:
                    flow = self.coupon_rate / self.frequency * last_pcp
                    pv = flow * df
                    px += pv
                if dt == next_rdp:  # 当提前偿还发生时的现金流
                    flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                    count += 1
                    pv = flow * df
                    px += pv
                    next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0

        px += df * last_pcp
        px = px / df_settle

        return px * self.par

    def clean_price_from_ytm(self):
        """ 通过YTM计算净价 """
        full_price = self.full_price_from_ytm()
        accrued_amount = self._accrued_interest
        clean_Price = full_price - accrued_amount
        return clean_Price

    def full_price_from_discount_curve(self):
        """ 通过利率曲线计算全价 """

        if self.settlement_date > self.due_date:
            raise TuringError("Bond settles after it matures.")

        px = 0.0
        df = 1.0
        df_settle = self._discount_curve.df(self.settlement_date)
        for rdp in range(len(self.pay_dates)):
            if self.settlement_date < self.pay_dates[rdp]:
                break
        next_rdp = self.pay_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0

        for dt in self._flow_dates[1:]:

            if dt >= self.settlement_date:  # 将结算日的票息加入计算
                df = self._discount_curve.df(dt)
                if dt < next_rdp:
                    flow = self.coupon_rate / self.frequency * last_pcp
                    pv = flow * df
                    px += pv
                if dt == next_rdp:  # 当提前偿还发生时的现金流
                    flow = self.coupon_rate / self.frequency * last_pcp + self.pay_rates[rdp - 1 + count]
                    count += 1
                    pv = flow * df
                    px += pv
                    next_rdp = self.pay_dates[rdp + count] if ((rdp + count) < len(self.pay_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.pay_dates)) else 0

        px += df * last_pcp
        px = px / df_settle

        return px * self.par

    def clean_price_from_discount_curve(self):
        """ 通过利率曲线计算净价 """

        self.calc_accrued_interest()
        full_price = self.full_price_from_discount_curve()

        accrued = self._accrued_interest
        clean_price = full_price - accrued
        return clean_price

    def current_yield(self):
        """ 当前收益 = 票息/净价 """

        y = self.coupon_rate * self.par / self._clean_price
        return y

    def yield_to_maturity(self):
        """ 通过一维求根器计算YTM """

        clean_price = self._clean_price
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

    def calc_accrued_interest(self):
        """ 应计利息 """

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

        for rdp in range(len(self.pay_dates)):
            if self.settlement_date < self.pay_dates[rdp]:
                break
        accr_base = self.remaining_principal[rdp - 1]

        if self.settlement_date > ex_dividend_date:  # 如果结算日大于除息日，减去一期
            acc_factor = acc_factor - 1.0 / self.frequency

        self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
        self._accrued_interest = acc_factor * self.par * accr_base * self.coupon_rate
        self._accrued_days = num

        return self._accrued_interest

    def check_ecnomic_terms(self):
        """检测ecnomic_terms是否为字典格式，若为字典格式，则处理成EcnomicTerms的实例对象"""
        ecnomic_terms = getattr(self, 'ecnomic_terms', None)
        if ecnomic_terms is not None and isinstance(ecnomic_terms, dict):
            prepayment_terms = PrepaymentTerms(data=ecnomic_terms.get('prepayment_terms'))
            ecnomic_terms = EcnomicTerms(prepayment_terms)
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
