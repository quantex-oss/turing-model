from dataclasses import dataclass, field
from typing import Union, List, Any

import numpy as np
from scipy import optimize

from fundamental.turing_db.bond_data import BondApi
from fundamental.turing_db.data import TuringDB
from turing_models.instruments.credit.bond import Bond, dy
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.day_count import TuringDayCount, TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringYTMCalcType
from turing_models.utilities.helper_functions import to_string
from turing_models.market.curves.curve_adjust import CurveAdjust
from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros


def _f(y, *args):
    """ Function used to do root search in price to yield calculation. """
    bond = args[0]
    price = args[1]
    bond.ytm = y
    px = bond.full_price_from_ytm()
    obj_fn = px - price
    return obj_fn


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondFixedRate(Bond):
    coupon: float = 0.0  # 票息
    curve_code: str = None  # 曲线编码
    zero_dates: List[Any] = field(default_factory=list)  # 支持手动传入曲线（日期）
    zero_rates: List[Any] = field(default_factory=list)  # 支持手动传入曲线（利率）
    _ytm: float = None
    _discount_curve = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        if self.coupon:
            self._calculate_flow_amounts()

    @property
    def get_yield_curve(self):
        return TuringDB.yield_curve(curve_code=self.curve_code, date=self.settlement_date_, df=False)[self.curve_code]

    @property
    def zero_dates_(self):
        return self.zero_dates or self.get_yield_curve['tenor']

    @property
    def zero_rates_(self):
        return self.zero_rates or self.get_yield_curve['spot_rate']

    @property
    def ytm(self):
        return self._ytm or self.ctx_ytm or self.yield_to_maturity()

    @ytm.setter
    def ytm(self, value: float):
        self._ytm = value

    def curve_adjust(self):
        """ 支持曲线旋转及平移 """
        ca = CurveAdjust(self.zero_dates_,  # 曲线信息
                         self.zero_rates_,
                         self.ctx_parallel_shift,  # 平移量（bps)
                         self.ctx_curve_shift,  # 旋转量（bps)
                         self.ctx_pivot_point,  # 旋转点（年）
                         self.ctx_tenor_start,  # 旋转起始（年）
                         self.ctx_tenor_end)  # 旋转终点（年）
        return ca.get_dates_result(), ca.get_rates_result()

    @property
    def zero_dates_adjusted(self):
        if self.ctx_parallel_shift:
            return self.curve_adjust()[0]
        else:
            return self.zero_dates_

    @property
    def zero_rates_adjusted(self):
        if self.ctx_parallel_shift:
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
    def discount_curve_flat(self):
        return TuringDiscountCurveFlat(self.settlement_date_,
                                       self.ytm)

    @property
    def clean_price_(self):
        return self.clean_price or self.clean_price_from_discount_curve()

    def _calculate_flow_amounts(self):
        """ 保存票息现金流信息 """

        self._flow_amounts = [0.0]

        for _ in self._flow_dates[1:]:
            cpn = self.coupon / self.frequency
            self._flow_amounts.append(cpn)

    def dv01(self):
        """ 数值法计算dv01 """
        ytm = self.ytm
        self.ytm = ytm - dy
        p0 = self.full_price_from_ytm()
        self.ytm = ytm + dy
        p2 = self.full_price_from_ytm()
        self.ytm = None
        dv = -(p2 - p0) / 2.0
        return dv

    def macauley_duration(self):
        """ 麦考利久期 """

        if self.settlement_date_ > self.due_date:
            raise TuringError("Bond settles after it matures.")

        discount_curve_flat = self.discount_curve_flat

        px = 0.0
        df = 1.0
        df_settle = discount_curve_flat.df(self.settlement_date_)
        dc = TuringDayCount(TuringDayCountTypes.ACT_ACT_ISDA)

        for dt in self._flow_dates[1:]:

            dates = dc.yearFrac(self.settlement_date_, dt)[0]
            # 将结算日的票息加入计算
            if dt >= self.settlement_date_:
                df = discount_curve_flat.df(dt)
                flow = self.coupon / self.frequency
                pv = flow * df * dates * self.par
                px += pv

        px += df * self._redemption * self.par * dates
        px = px / df_settle

        self.discount_curve = discount_curve_flat
        fp = self.full_price_from_discount_curve()
        self.discount_curve = None

        dmac = px / fp

        return dmac

    def modified_duration(self):
        """ 修正久期 """

        dmac = self.macauley_duration()
        md = dmac / (1.0 + self.ytm / self.frequency)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        ytm = self.ytm
        self.ytm = ytm - dy
        p0 = self.full_price_from_ytm()
        self.ytm = ytm
        p1 = self.full_price_from_ytm()
        self.ytm = ytm + dy
        p2 = self.full_price_from_ytm()
        self.ytm = None
        dollar_conv = ((p2 + p0) - 2.0 * p1) / dy / dy
        return dollar_conv

    def full_price_from_ytm(self):
        """ 通过YTM计算全价 """
        self.calc_accrued_interest()

        ytm = np.array(self.ytm)  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0

        f = self.frequency
        c = self.coupon
        v = 1.0 / (1.0 + ytm / f)

        # n是下一付息日后的现金流个数
        n = 0
        for dt in self._flow_dates:
            if dt > self.settlement_date_:
                n += 1
        n = n - 1

        if n < 0:
            raise TuringError("No coupons left")

        if self.convention == TuringYTMCalcType.UK_DMO:
            if n == 0:
                fp = (v ** (self._alpha)) * (self._redemption + c / f)
            else:
                term1 = (c / f)
                term2 = (c / f) * v
                term3 = (c / f) * v * v * (1.0 - v ** (n - 1)) / (1.0 - v)
                term4 = self._redemption * (v ** n)
                fp = (v ** (self._alpha)) * (term1 + term2 + term3 + term4)
        elif self.convention == TuringYTMCalcType.US_TREASURY:
            if n == 0:
                fp = (v ** (self._alpha)) * (self._redemption + c / f)
            else:
                term1 = (c / f)
                term2 = (c / f) * v
                term3 = (c / f) * v * v * (1.0 - v ** (n - 1)) / (1.0 - v)
                term4 = self._redemption * (v ** n)
                vw = 1.0 / (1.0 + self._alpha * ytm / f)
                fp = (vw) * (term1 + term2 + term3 + term4)
        elif self.convention == TuringYTMCalcType.US_STREET:
            vw = 1.0 / (1.0 + self._alpha * ytm / f)
            if n == 0:
                vw = 1.0 / (1.0 + self._alpha * ytm / f)
                fp = vw * (self._redemption + c / f)
            else:
                term1 = (c / f)
                term2 = (c / f) * v
                term3 = (c / f) * v * v * (1.0 - v ** (n - 1)) / (1.0 - v)
                term4 = self._redemption * (v ** n)
                fp = (v ** (self._alpha)) * (term1 + term2 + term3 + term4)
        else:
            raise TuringError("Unknown yield convention")

        return fp * self.par

    def clean_price_from_ytm(self):
        """ 通过YTM计算净价 """
        full_price = self.full_price_from_ytm()
        accrued_amount = self._accrued_interest
        clean_Price = full_price - accrued_amount
        return clean_Price

    def full_price_from_discount_curve(self):
        """ 通过利率曲线计算全价 """

        if self.settlement_date_ < self.discount_curve._valuationDate:
            raise TuringError("Bond settles before Discount curve date")

        if self.settlement_date_ > self.due_date:
            raise TuringError("Bond settles after it matures.")

        px = 0.0
        df = 1.0
        df_settle = self.discount_curve.df(self.settlement_date_)

        for dt in self._flow_dates[1:]:

            # 将结算日的票息加入计算
            if dt >= self.settlement_date_:
                df = self.discount_curve.df(dt)
                flow = self.coupon / self.frequency
                pv = flow * df
                px += pv

        px += df * self._redemption
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

    def _resolve(self):
        # Bond_ 为自定义时自动生成
        if self.asset_id and not self.asset_id.startswith("Bond_"):
            bond = BondApi.fetch_one_bond_orm(asset_id=self.asset_id)
            for k, v in bond.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        self.set_ytm()
        self.set_curve()
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        s += to_string("Coupon", self.coupon)
        s += to_string("Curve Code", self.curve_code)
        if self.ytm:
            s += to_string("YTM", self.ytm)
        return s
