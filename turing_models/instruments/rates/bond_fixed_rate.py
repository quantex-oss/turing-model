from dataclasses import dataclass

import numpy as np
from scipy import optimize

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import greek, newton_fun
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.utilities.calendar import TuringCalendar
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import CouponType, TuringYTMCalcType
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondFixedRate(Bond):
    __clean_price: float = None
    __ytm: float = None
    __discount_curve = None
    __spread_adjustment = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ex_dividend_days = 0
        self._alpha = 0.0
        if self.coupon_rate:
            self._calculate_cash_flow_amounts()

    @property
    def _spread_adjustment(self):
        return self.__spread_adjustment or self.ctx_spread_adjustment

    @_spread_adjustment.setter
    def _spread_adjustment(self, value: float):
        self.__spread_adjustment = value

    def ytm(self):
        """定价服务调用"""
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self._ytm

    @property
    def _ytm(self):
        return self.__ytm or self.ctx_ytm or self.yield_to_maturity()

    @_ytm.setter
    def _ytm(self, value: float):
        self.__ytm = value

    @property
    def _market_clean_price(self):
        date = self._settlement_date.datetime()
        original_data = TuringDB.get_bond_valuation_cnbd_history(symbols=self.comb_symbol, start=date, end=date)
        if original_data is not None:
            data = original_data.loc[self.comb_symbol].loc[0, 'net_prc']
            return data
        else:
            raise TuringError(f"Cannot find cnbd bond clean price for {self.comb_symbol}")

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

    def clean_price(self):
        # 定价接口调用
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self._clean_price

    def full_price(self):
        # 定价接口调用
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return self._clean_price + self.calc_accrued_interest()

    def _calculate_cash_flow_amounts(self):
        """ 保存票息现金流信息 """

        self._flow_amounts = [0.0]
        if getattr(self, 'pay_interest_mode', None) and \
           getattr(self, 'coupon_rate', None) and \
           getattr(self, 'bond_term_year', None) and \
           getattr(self, 'frequency', None):
            for _ in self._flow_dates[1:]:
                if self.pay_interest_mode == CouponType.DISCOUNT:
                    cpn = 0
                elif self.pay_interest_mode == CouponType.ZERO_COUPON:
                    cpn = self.coupon_rate * self.bond_term_year
                elif self.pay_interest_mode == CouponType.COUPON_CARRYING:
                    cpn = self.coupon_rate / self.frequency
                self._flow_amounts.append(cpn)

    def implied_spread(self):
        """ 通过行情价格和隐含利率曲线推算债券的隐含基差"""

        self.calc_accrued_interest()
        full_price = self._market_clean_price + self._accrued_interest

        argtuple = (self, full_price, '_spread_adjustment', 'full_price_from_discount_curve')

        implied_spread = optimize.newton(newton_fun,
                                         x0=0.05,  # guess initial value of 5%
                                         fprime=None,
                                         args=argtuple,
                                         tol=1e-8,
                                         maxiter=50,
                                         fprime2=None)
        self.__spread_adjustment = None

        return implied_spread

    def dv01(self):
        """ 数值法计算dv01 """
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy

    def macauley_duration(self):
        """ 麦考利久期 """
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        self._curve_resolve()  # 要调用曲线对象前需要先调用curve_resolve，用以兼容what-if
        self.curve_fitted = CurveAdjustmentImpl(curve_data=self.cv.curve_data,
                                                parallel_shift=self._spread_adjustment,
                                                value_date=self._settlement_date).get_curve_result()

        px = 0.0
        df = 1.0
        df_settle = self.curve_fitted.df(self._settlement_date)
        dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

        for dt in self._flow_dates[1:]:

            dates = dc.yearFrac(self._settlement_date, dt)[0]
            # 将结算日的票息加入计算
            if dt >= self._settlement_date:
                df = self.curve_fitted.df(dt)
                if self.pay_interest_mode == CouponType.COUPON_CARRYING:
                    flow = self.coupon_rate / self.frequency
                    pv = flow * df * dates * self.par
                    px += pv
                else:
                    flow = self._flow_amounts[-1]
                    pv = flow * df * dates * self.par
                    px += pv

        px += df * self._redemption * self.par * dates
        px = px / df_settle

        fp = self.full_price_from_ytm()
        dmac = px / fp

        return dmac

    def modified_duration(self):
        """ 修正久期 """
        dmac = self.macauley_duration()
        if self.pay_interest_mode == CouponType.COUPON_CARRYING:
            md = dmac / (1.0 + self._ytm / self.frequency)
        else:
            md = dmac / (1.0 + self._ytm * self.time_to_maturity_in_year)
        return md

    def dollar_convexity(self):
        """ 凸性 """
        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        return greek(self, self.full_price_from_ytm, "_ytm", order=2)

    def full_price_from_ytm(self):
        """ 通过YTM计算全价 """
        # https://www.dmo.gov.uk/media/15004/convention_changes.pdf
        
        self.calc_accrued_interest()

        ytm = np.array(self._ytm)  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0
        if self.pay_interest_mode == CouponType.COUPON_CARRYING:
            f = self.frequency
            c = self.coupon_rate
            v = 1.0 / (1.0 + ytm / f)

            # n是下一付息日后的现金流个数
            n = 0
            for dt in self._flow_dates:
                if dt > self._settlement_date:
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
        
        else:
            if self.time_to_maturity_in_year <= 1:
                fp = (self._redemption + self._flow_amounts[-1]) * self.par / (ytm * self.time_to_maturity_in_year + 1)
            else:
                fp = ((self._redemption + self._flow_amounts[-1]) * self.par / (ytm + 1)) ** self.time_to_maturity_in_year
            return fp
                

    def clean_price_from_ytm(self):
        """ 通过YTM计算净价 """
        full_price = self.full_price_from_ytm()
        clean_Price = full_price - self._accrued_interest
        return clean_Price

    def full_price_from_discount_curve(self):
        """ 通过利率曲线计算全价 """

        if not self.isvalid():
            raise TuringError("Bond settles after it matures.")
        self._curve_resolve()  # 要调用曲线对象前需要先调用curve_resolve，用以兼容what-if
        self.curve_fitted = CurveAdjustmentImpl(curve_data=self.cv.curve_data,
                                                parallel_shift=self._spread_adjustment,
                                                value_date=self._settlement_date).get_curve_result()

        px = 0.0
        df = 1.0
        df_settle = self.curve_fitted.df(self._settlement_date)

        for dt in self._flow_dates[1:]:

            # 将结算日的票息加入计算
            if dt >= self._settlement_date:
                df = self.curve_fitted.df(dt)
                if self.pay_interest_mode == CouponType.COUPON_CARRYING:
                    flow = self.coupon_rate / self.frequency
                    pv = flow * df
                    px += pv
                else:
                    flow = self._flow_amounts[-1]
                    pv = flow * df
                    px += pv

        px += df * self._redemption
        px = px / df_settle

        return px * self.par

    def clean_price_from_discount_curve(self):
        """ 通过利率曲线计算净价 """

        self.calc_accrued_interest()
        full_price = self.full_price_from_discount_curve()
        clean_price = full_price - self._accrued_interest
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
        full_prices = clean_prices + self._accrued_interest
        ytms = []

        for full_price in full_prices:
            argtuple = (self, full_price, '_ytm', 'full_price_from_ytm')

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
            if self._flow_dates[i_flow] >= self._settlement_date:
                self._pcd = self._flow_dates[i_flow - 1]  # 结算日前一个现金流
                self._ncd = self._flow_dates[i_flow]  # 结算日后一个现金流
                break

        dc = TuringDayCount(self.interest_rules)
        cal = TuringCalendar(self.calendar_type)
        ex_dividend_date = cal.addBusinessDays(
            self._ncd, -self.num_ex_dividend_days)  # 除息日
        
        if self.pay_interest_mode == CouponType.COUPON_CARRYING:
            (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                               self._settlement_date,
                                               self._ncd,
                                               self.pay_interest_cycle)  # 计算应计日期，返回应计因数、应计天数、基数
            
            if self._settlement_date > ex_dividend_date:  # 如果结算日大于除息日，减去一期
                acc_factor = acc_factor - 1.0 / self.frequency
            
            self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
                
            
        else:
            (acc_factor, num, _) = dc.yearFrac(self._pcd,
                                               self._settlement_date)
        self._accrued_interest = acc_factor * self.par * self.coupon_rate
        self._accrued_days = num

        return self._accrued_interest

    def _resolve(self):
        super()._resolve()
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        return s
