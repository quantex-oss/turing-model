import datetime
from dataclasses import dataclass

import numpy as np
from tunny import model, compute
from fundamental.base import Context, ctx
from fundamental.market.curves import TuringDiscountCurveFlat

from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.global_variables import gDaysInYear, gNumObsInYear
from turing_models.utilities.global_types import TuringKnockOutTypes
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme


bump = 1e-4


@model
@dataclass
class KnockOutOption:
    """
        Instrument definition for equity option
        支持多种参数传入方式
        Examples:
        1.
        # >>> eq = EqOption(asset_id='123', option_type='CALL', product_type='European', expiry=TuringDate(2021, 2, 12), strike_price=90, multiplier=10000)
        # >>> eq.from_json()
        # >>> eq.price()
        2.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
        3.
        # >>> _option = Option()
        # >>> _option.resolve(_resource=somedict)
        # >>> eq = EqOption(option_type='CALL',product_type='European', notional=1.00, obj=_option)
        # >>> eq.resolve()
        # >>> eq.price()
    """

    asset_id: str = None
    quantity: float = None
    underlier: str = None
    product_type: str = None
    option_type: str = None
    notional: float = None
    initial_spot: float = None
    number_of_options: float = None
    start_date: str = None
    end_date: str = None
    expiry: str = None
    start_averaging_date: str = None
    participation_rate: float = None
    strike_price: float = None
    barrier: float = None
    rebate: float = None
    coupon: float = None
    multiplier: float = None
    currency: str = None
    premium: float = None
    premium_date: str = None
    knock_in_price: float = None
    annualized_flag: bool = True
    knock_out_type: str = None
    knock_in_type: str = None
    knock_in_strike1: float = None
    knock_in_strike2: float = None
    accrued_average: float = None
    value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))  # 估值日期
    stock_price: float = None
    volatility: float = 0.1
    interest_rate: float = 0.02
    dividend_yield: float = 0
    ctx: Context = ctx
    __property_data = {
        "value_date": None,
        "_value_date": None,
        "stock_price": None,
        "_stock_price": None,
        "v": None,
        "_v": None,
        "discount_curve": None,
        "_discount_curve": None,
        "dividend_curve": None,
        "_dividend_curve": None
    }

    def __post_init__(self):
        self.set_param()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 10000
        self.seed = 4242

    def set_param(self):
        self._value_date = self.value_date
        self._stock_price = self.stock_price
        self._volatility = self.volatility
        self._interest_rate = self.interest_rate
        self._dividend_yield = self.dividend_yield

    def _set_by_dict(self, tmp_dict):
        for k, v in tmp_dict.items():
            setattr(self, k, v)

    def resolve(self, expand_dict):
        self._set_by_dict(expand_dict)
        self.set_param()

    @property
    def value_date_(self):
        self.__property_data["value_date"] = self.ctx.pricing_date or self._value_date
        if self.__property_data["_value_date"] is None:
            return self.__property_data["value_date"]
        else:
            return self.__property_data["_value_date"]

    @value_date_.setter
    def value_date_(self, value: TuringDate):
        self.__property_data["_value_date"] = value

    @property
    def stock_price_(self) -> float:
        self.__property_data["stock_price"] = getattr(self.ctx, f"spot_{self.underlier}") or self._stock_price
        if self.__property_data["_stock_price"] is None:
            return self.__property_data["stock_price"]
        else:
            return self.__property_data["_stock_price"]

    @stock_price_.setter
    def stock_price_(self, value: float):
        self.__property_data["_stock_price"] = value

    @property
    def volatility_(self) -> float:
        return getattr(self.ctx, f"volatility_{self.underlier}") or self._volatility

    @property
    def interest_rate_(self) -> float:
        return self.ctx.interest_rate or self.interest_rate

    @property
    def dividend_yield_(self) -> float:
        return self.ctx.dividend_yield or self._dividend_yield

    @property
    def model(self) -> TuringModelBlackScholes:
        return TuringModelBlackScholes(self.volatility_)

    @property
    def discount_curve(self) -> TuringDiscountCurveFlat:
        self.__property_data["discount_curve"] = TuringDiscountCurveFlat(
            self.value_date_, self.interest_rate_)
        if self.__property_data["_discount_curve"] is None:
            return self.__property_data["discount_curve"]
        else:
            return self.__property_data["_discount_curve"]

    @discount_curve.setter
    def discount_curve(self, value: TuringDiscountCurveFlat):
        self.__property_data["_discount_curve"] = value

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        self.__property_data["dividend_curve"] = TuringDiscountCurveFlat(
            self.value_date_, self.dividend_yield_)
        if self.__property_data["_dividend_curve"] is None:
            return self.__property_data["dividend_curve"]
        else:
            return self.__property_data["_dividend_curve"]

    @dividend_curve.setter
    def dividend_curve(self, value: TuringDiscountCurveFlat):
        self.__property_data["_dividend_curve"] = value

    @property
    def texp(self) -> float:
        return (self.expiry - self.value_date_) / gDaysInYear

    @property
    def r(self) -> float:
        df = self.discount_curve.df(self.expiry)
        return -np.log(df)/self.texp

    @property
    def q(self) -> float:
        dq = self.dividend_curve.df(self.expiry)
        return -np.log(dq)/self.texp

    @property
    def v(self) -> float:
        self.__property_data["v"] = self.model._volatility
        if self.__property_data["_v"] is None:
            return self.__property_data["v"]
        else:
            return self.__property_data["_v"]

    @v.setter
    def v(self, value: float):
        self.__property_data["_v"] = value

    @property
    def knock_out_type_(self) -> TuringKnockOutTypes:
        return TuringKnockOutTypes.UP_AND_OUT_CALL if self.knock_out_type == 'up_and_out' \
            else TuringKnockOutTypes.DOWN_AND_OUT_PUT

    def price(self) -> float:
        s0 = self.stock_price_
        k = self.strike_price
        b = self.barrier
        r = self.r
        q = self.q
        vol = self.v
        rebate = self.rebate
        notional = self.notional
        texp = self.texp
        knock_out_type = self.knock_out_type_
        flag = self.annualized_flag
        participation_rate = self.participation_rate
        num_ann_obs = self.num_ann_obs
        num_paths = self.num_paths
        seed = self.seed

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL and s0 >= b:
            return rebate * texp**flag * notional * np.exp(-r * texp)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT and s0 <= b:
            return rebate * texp**flag * notional * np.exp(-r * texp)

        process = TuringProcessSimulator()
        process_type = TuringProcessTypes.GBM
        scheme = TuringGBMNumericalScheme.ANTITHETIC
        model_params = (s0, r-q, vol, scheme)

        Sall = process.getProcess(process_type, texp, model_params,
                                  num_ann_obs, num_paths, seed)

        (num_paths, _) = Sall.shape

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            barrierCrossedFromBelow = [False] * num_paths
            for p in range(0, num_paths):
                barrierCrossedFromBelow[p] = np.any(Sall[p] >= b)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            barrierCrossedFromAbove = [False] * num_paths
            for p in range(0, num_paths):
                barrierCrossedFromAbove[p] = np.any(Sall[p] <= b)

        payoff = np.zeros(num_paths)
        ones = np.ones(num_paths)

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            payoff = np.maximum((Sall[:, -1] - k) / s0, 0.0) * \
                        participation_rate * (ones - barrierCrossedFromBelow) + \
                        rebate * texp**flag * (ones * barrierCrossedFromBelow)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            payoff = np.maximum((k - Sall[:, -1]) / s0, 0.0) * \
                        participation_rate * (ones - barrierCrossedFromAbove) + \
                        rebate * texp**flag * (ones * barrierCrossedFromAbove)

        return payoff.mean() * np.exp(- r * texp) * notional

    def eq_delta(self) -> float:
        return greek(self, self.price, "stock_price_")

    def eq_gamma(self) -> float:
        return greek(self, self.price, "stock_price_", order=2)

    def eq_vega(self) -> float:
        return greek(self, self.price, "v")

    def eq_theta(self) -> float:
        day_diff = 1
        bump_local = day_diff / gDaysInYear
        return greek(self, self.price, "value_date_", bump=bump_local,
                     cus_inc=(self.value_date_.addDays, day_diff))

    def eq_rho(self) -> float:
        return greek(self, self.price, "discount_curve",
                     cus_inc=(self.discount_curve.bump, bump))

    def eq_rho_q(self) -> float:
        return greek(self, self.price, "dividend_curve",
                     cus_inc=(self.dividend_curve.bump, bump))


def greek(obj, price, attr, bump=bump, order=1, cus_inc=None):
    """
    如果要传cus_inc，格式须为(函数名, 函数参数值)
    """
    cus_func = args = None
    attr_value = getattr(obj, attr)
    if cus_inc:
        cus_func, args = cus_inc

    def increment(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(args*count)
        else:
            _attr_value += count * bump
        setattr(obj, attr, _attr_value)

    def decrement(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(-args*count)
        else:
            _attr_value -= count * bump
        setattr(obj, attr, _attr_value)

    def clear():
        setattr(obj, attr, None)

    if order == 1:
        p0 = price()
        increment(attr_value)
        p_up = price()
        clear()
        return (p_up - p0) / bump
    elif order == 2:
        p0 = price()
        decrement(attr_value)
        p_down = price()
        increment(attr_value)
        p_up = price()
        clear()
        return (p_up - 2.0 * p0 + p_down) / bump / bump
