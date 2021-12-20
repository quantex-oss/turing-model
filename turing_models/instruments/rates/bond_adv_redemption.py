from dataclasses import dataclass, field
from typing import Union, List, Any

import numpy as np
from scipy import optimize

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import newton_fun
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.helper_functions import to_string
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondAdvRedemption(Bond):
    coupon: float = 0.0  # 票息
    rdp_dates: List[Any] = field(default_factory=list)  # 提前偿还各期日期
    rdp_pct: List[Any] = field(default_factory=list)  # 提前偿还各期百分比
    _ytm: float = None
    _discount_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        if len(self.rdp_dates) != len(self.rdp_pct):
            raise TuringError("redemption terms should match redemption percents.")
        if sum(self.rdp_pct) != 1:
            raise TuringError("total redemption doesn't equal to 1.")
        self._calculate_rdp_pcp()
        if self.coupon:
            self._calculate_flow_amounts()
            
    @property
    def ytm_(self):
        return self._ytm or self.ctx_ytm or self.yield_to_maturity()

    @ytm_.setter
    def ytm_(self, value: float):
        self._ytm = value

    def ytm(self):
        # 定价接口调用
        return self.ytm_

    def full_price(self):
        # 定价接口调用
        return self.full_price_from_discount_curve()

    def clean_price(self):
        # 定价接口调用
        return self.clean_price_

    def _calculate_rdp_pcp(self):
        """ Determine the bond remaining principal."""

        self.rdp_dates.insert(0, self.issue_date)
        self.remaining_principal = [1]
        for i in range(len(self.rdp_dates)-1):
            self.remaining_principal.append(self.remaining_principal[i] - self.rdp_pct[i])
        
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
    def clean_price_(self):
        return self.ctx_clean_price or self.clean_price_from_discount_curve()

    def _calculate_flow_amounts(self):
        """ 保存票息现金流信息 """

        self._flow_amounts = [0.0]

        for _ in self._flow_dates[1:]:
            cpn = self.coupon / self.frequency
            self._flow_amounts.append(cpn)

    def dv01(self):
        """ 数值法计算dv01 """
        ytm = self.ytm_
        self.ytm_ = ytm - dy
        p0 = self.full_price_from_ytm()
        self.ytm_ = ytm + dy
        p2 = self.full_price_from_ytm()
        self.ytm_ = None
        dv = -(p2 - p0) / 2.0
        return dv

    def macauley_duration(self):
        """ 麦考利久期 """

        if self.settlement_date_ > self.due_date:
            raise TuringError("Bond settles after it matures.")

        discount_curve_flat = TuringDiscountCurveFlat(self.settlement_date_, self.ytm_)

        px = 0.0
        df = 1.0
        df_settle = self.discount_curve_flat.df(self.settlement_date_)
        for rdp in range(len(self.rdp_dates)):
            if self.settlement_date_ < self.rdp_dates[rdp]:
                break
        next_rdp = self.rdp_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0
        dc = TuringDayCount(TuringDayCountTypes.ACT_ACT_ISDA)

        for dt in self._flow_dates[1:]:
            dates = dc.yearFrac(self.settlement_date_, dt)[0]
            if dt >= self.settlement_date_:  # 将结算日的票息加入计算
                df = discount_curve_flat.df(dt)
                if dt < next_rdp:
                    flow = self.coupon / self.frequency * last_pcp
                    pv = flow * df * self.par * dates
                    px += pv
                if dt == next_rdp:  # 当提前偿还发生时的现金流
                    flow = self.coupon / self.frequency * last_pcp + self.rdp_pct[rdp]
                    count += 1
                    pv = flow * df * dates * self.par
                    px += pv
                    next_rdp = self.rdp_dates[rdp + count] if ((rdp + count) < len(self.rdp_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.rdp_dates)) else 0

        px += df * last_pcp * self.par * dates
        px = px / df_settle

        self.discount_curve = discount_curve_flat
        fp = self.full_price_from_discount_curve()
        self.discount_curve = None

        dmac = px / fp

        return dmac

    def modified_duration(self):
        """ 修正久期 """

        dmac = self.macauley_duration()
        md = dmac / (1.0 + self.ytm_ / self.frequency)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        ytm = self.ytm_
        self.ytm_ = ytm - dy
        p0 = self.full_price_from_ytm()
        self.ytm_ = ytm
        p1 = self.full_price_from_ytm()
        self.ytm_ = ytm + dy
        p2 = self.full_price_from_ytm()
        self.ytm_ = None
        dollar_conv = ((p2 + p0) - 2.0 * p1) / dy / dy
        return dollar_conv

    def full_price_from_ytm(self):
        """ 通过YTM计算全价 """
        self.calc_accrued_interest()

        ytm = np.array(self.ytm_)  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0

        if self.settlement_date_ > self.due_date:
            raise TuringError("Bond settles after it matures.")
        
        discount_curve_flat = TuringDiscountCurveFlat(self.settlement_date_, self.ytm_, self.freq_type, self.accrual_type)

        px = 0.0
        df = 1.0
        df_settle = discount_curve_flat.df(self.settlement_date_)
        for rdp in range(len(self.rdp_dates)):
            if self.settlement_date_ < self.rdp_dates[rdp]:
                break
        next_rdp = self.rdp_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0

        for dt in self._flow_dates[1:]:

            if dt >= self.settlement_date_:  # 将结算日的票息加入计算
                df = discount_curve_flat.df(dt)
                if dt < next_rdp:
                    flow = self.coupon / self.frequency * last_pcp
                    pv = flow * df
                    px += pv
                if dt == next_rdp:  # 当提前偿还发生时的现金流
                    flow = self.coupon / self.frequency * last_pcp + self.rdp_pct[rdp]
                    count += 1
                    pv = flow * df
                    px += pv
                    next_rdp = self.rdp_dates[rdp + count] if ((rdp + count) < len(self.rdp_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.rdp_dates)) else 0

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

        if self.settlement_date_ > self.due_date:
            raise TuringError("Bond settles after it matures.")

        px = 0.0
        df = 1.0
        df_settle = self.discount_curve.df(self.settlement_date_)
        for rdp in range(len(self.rdp_dates)):
            if self.settlement_date_ < self.rdp_dates[rdp]:
                break
        next_rdp = self.rdp_dates[rdp]  # 下个提前偿还日
        last_pcp = self.remaining_principal[rdp - 1]  # 剩余本金
        count = 0

        for dt in self._flow_dates[1:]:

            if dt >= self.settlement_date_:  # 将结算日的票息加入计算
                df = self.discount_curve.df(dt)
                if dt < next_rdp:
                    flow = self.coupon / self.frequency * last_pcp
                    pv = flow * df
                    px += pv
                if dt == next_rdp:  # 当提前偿还发生时的现金流
                    flow = self.coupon / self.frequency * last_pcp + self.rdp_pct[rdp]
                    count += 1
                    pv = flow * df
                    px += pv
                    next_rdp = self.rdp_dates[rdp + count] if ((rdp + count) < len(self.rdp_dates)) else 0
                    last_pcp = self.remaining_principal[rdp - 1 + count] if ((rdp + count) < len(self.rdp_dates)) else 0

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

        y = self.coupon * self.par / self.clean_price_
        return y

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
            argtuple = (self, full_price, "ytm_", "full_price_from_ytm")

            ytm = optimize.newton(newton_fun,
                                  x0=0.05,  # guess initial value of 5%
                                  fprime=None,
                                  args=argtuple,
                                  tol=1e-8,
                                  maxiter=50,
                                  fprime2=None)

            ytms.append(ytm)
            self.ytm_ = None

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

        for rdp in range(len(self.rdp_dates)):
            if self.settlement_date_ < self.rdp_dates[rdp]:
                break
        accr_base = self.remaining_principal[rdp - 1]

        if self.settlement_date_ > ex_dividend_date:  # 如果结算日大于除息日，减去一期
            acc_factor = acc_factor - 1.0 / self.frequency

        self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
        self._accrued_interest = acc_factor * self.par * accr_base * self.coupon
        self._accrued_days = num

        return self._accrued_interest

    def __repr__(self):
        s = super().__repr__()
        s += to_string("Coupon", self.coupon)
        s += to_string("Curve Code", self.curve_code)
        return s
