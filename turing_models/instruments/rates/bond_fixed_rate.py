from dataclasses import dataclass

import numpy as np
from scipy import optimize

from fundamental.turing_db.data import TuringDB
from turing_models.instruments.common import newton_fun, YieldCurve
from turing_models.instruments.rates.bond import Bond, dy
from turing_models.utilities.day_count import TuringDayCount, DayCountType
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import CouponType, TuringYTMCalcType
from turing_models.market.curves.curve_adjust import CurveAdjustmentImpl
from turing_models.utilities.helper_functions import calculate_greek, to_turing_date


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BondFixedRate(Bond):

    def __post_init__(self):
        super().__post_init__()

    def _init(self):
        super()._init()
        self._num_ex_dividend_days = 0
        self._spread_adjustment = 0
        if self.issue_date:
            self.cv = YieldCurve(value_date=self.value_date, curve_code=self.curve_code)
            if self.curve_code is not None:
                self.cv.resolve()
        self._calculate_cash_flow_amounts()
        if getattr(self, 'issue_date', None) is not None:
            self._calc_accrued_interest()
            self._clean_price = self.clean_price_from_discount_curve()
            self._ytm = self.yield_to_maturity()

    def _save_original_data(self):
        """ 存储未经ctx修改的属性值，存储在字典中 """
        super()._save_original_data()
        self._original_data['_spread_adjustment'] = self._spread_adjustment

    def _adjust_data_based_on_ctx(self):
        super()._adjust_data_based_on_ctx()
        ctx_pricing_date = self.ctx_pricing_date
        ctx_spread_adjustment = self.ctx_spread_adjustment
        ctx_clean_price = self.ctx_clean_price
        ctx_ytm = self.ctx_ytm
        _original_data = self._original_data
        self._spread_adjustment = ctx_spread_adjustment or _original_data['_spread_adjustment']
        self._calc_accrued_interest()
        self._clean_price = ctx_clean_price or self.clean_price_from_discount_curve()
        self._ytm = ctx_ytm or self.yield_to_maturity()

    def _get_market_clean_price(self):
        if getattr(self, 'comb_symbol', None) is not None:
            original_data = TuringDB.get_bond_valuation_cnbd_history(symbols=self.comb_symbol,
                                                                     start=self.value_date,
                                                                     end=self.value_date)

            if not original_data.empty:
                self._market_clean_price = original_data.loc[self.comb_symbol]['net_prc'][0]
            else:
                raise TuringError(f"Cannot find cnbd bond clean price for {self.comb_symbol}")

    def ytm(self):
        """定价服务调用"""
        return self._ytm

    def clean_price(self):
        # 定价接口调用
        return self._clean_price

    def full_price(self):
        # 定价接口调用
        return self._clean_price + self._accrued_interest

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
        self._get_market_clean_price()

        full_price = self._market_clean_price + self._accrued_interest

        _spread_adjustment = self._spread_adjustment
        argtuple = (self, full_price, '_spread_adjustment', 'full_price_from_discount_curve')

        implied_spread = optimize.newton(newton_fun,
                                         x0=0.05,  # guess initial value of 5%
                                         fprime=None,
                                         args=argtuple,
                                         tol=1e-8,
                                         maxiter=50,
                                         fprime2=None)
        self._spread_adjustment = _spread_adjustment

        return implied_spread

    def dv01(self):
        """ 数值法计算dv01 """
        return calculate_greek(self, self.full_price_from_ytm, "_ytm", dy) * -dy

    def macauley_duration(self):
        """ 麦考利久期 """
        fitted_curve = CurveAdjustmentImpl(curve_data=self.cv.curve_data,
                                           parallel_shift=self._spread_adjustment,
                                           value_date=self.settlement_date).get_curve_result()

        px = 0.0
        df = 1.0
        df_settle = fitted_curve.df(self.settlement_date)
        dc = TuringDayCount(DayCountType.ACT_ACT_ISDA)

        for dt in self._flow_dates[1:]:

            dates = dc.yearFrac(self.settlement_date, dt)[0]
            # 将结算日的票息加入计算
            if dt >= self.settlement_date:
                df = fitted_curve.df(dt)
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
        return calculate_greek(self, self.full_price_from_ytm, "_ytm", order=2)

    def full_price_from_ytm(self):
        """ 通过YTM计算全价 """
        # https://www.dmo.gov.uk/media/15004/convention_changes.pdf

        ytm = np.array(self._ytm)  # 向量化
        ytm = ytm + 0.000000000012345  # 防止ytm = 0
        if self.pay_interest_mode == CouponType.COUPON_CARRYING:
            f = self.frequency
            c = self.coupon_rate
            v = 1.0 / (1.0 + ytm / f)

            # n是下一付息日后的现金流个数
            n = 0
            for dt in self._flow_dates:
                if dt > self.settlement_date:
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
        if getattr(self, 'pay_interest_mode', None) \
           and getattr(self, 'frequency', None) \
           and getattr(self, 'par', None):
            fitted_curve = CurveAdjustmentImpl(curve_data=self.cv.curve_data,
                                               parallel_shift=self._spread_adjustment,
                                               value_date=self.settlement_date).get_curve_result()

            px = 0.0
            df = 1.0
            df_settle = fitted_curve.df(self.settlement_date)

            for dt in self._flow_dates[1:]:

                # 将结算日的票息加入计算
                if dt >= self.settlement_date:
                    df = fitted_curve.df(dt)
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
        if getattr(self, '_accrued_interest', None) is not None:
            full_price = self.full_price_from_discount_curve()
            clean_price = full_price - self._accrued_interest
            return clean_price

    def current_yield(self):
        """ 当前收益 = 票息/净价 """

        y = self.coupon_rate * self.par / self._clean_price
        return y

    def yield_to_maturity(self):
        """ 通过一维求根器计算YTM """
        clean_price = getattr(self, '_clean_price', None)
        if clean_price is not None:
            if isinstance(clean_price, (float, int, np.float64)):
                clean_prices = np.array([clean_price])
            elif isinstance(clean_price, (list, np.ndarray)):
                clean_prices = np.array(clean_price)
            else:
                raise TuringError("Unknown type for clean_price "
                                  + str(type(clean_price)))

            full_prices = clean_prices + self._accrued_interest
            ytms = []
            _ytm = getattr(self, '_ytm', None)
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
            self._ytm = _ytm
            if len(ytms) == 1:
                return ytms[0]
            else:
                return np.array(ytms)

    def _calc_accrued_interest(self):
        """ 应计利息 """
        if getattr(self, '_flow_dates', None) is not None \
           and getattr(self, 'interest_rules', None) is not None \
           and getattr(self, 'pay_interest_mode', None) is not None \
           and getattr(self, 'frequency', None) is not None \
           and getattr(self, 'par', None) is not None \
           and getattr(self, 'coupon_rate', None) is not None \
           and getattr(self, 'settlement_date', None) is not None:
            num_flows = len(self._flow_dates)

            if num_flows == 0:
                raise TuringError("Accrued interest - not enough flow dates.")

            for i_flow in range(1, num_flows):
                if self._flow_dates[i_flow] >= self.settlement_date:
                    _pcd = self._flow_dates[i_flow - 1]  # 结算日前一个现金流
                    _ncd = self._flow_dates[i_flow]  # 结算日后一个现金流
                    break

            dc = TuringDayCount(self.interest_rules)
            # cal = TuringCalendar(self.calendar_type)
            ex_dividend_date = self.calendar.addBusinessDays(
                _ncd, -self._num_ex_dividend_days
            )  # 除息日

            if self.pay_interest_mode == CouponType.COUPON_CARRYING:
                acc_factor, num, _ = dc.yearFrac(_pcd,
                                                 self.settlement_date,
                                                 _ncd,
                                                 self.pay_interest_cycle)  # 计算应计日期，返回应计因数、应计天数、基数

                if self.settlement_date > ex_dividend_date:  # 如果结算日大于除息日，减去一期
                    acc_factor = acc_factor - 1.0 / self.frequency

                self._alpha = 1.0 - acc_factor * self.frequency  # 计算alpha值供全价计算公式使用
            else:
                acc_factor, num, _ = dc.yearFrac(_pcd,
                                                 self.settlement_date)
                self._alpha = 0.0
            self._accrued_interest = acc_factor * self.par * self.coupon_rate
            self._accrued_days = num

    def _resolve(self):
        super()._resolve()
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        return s
