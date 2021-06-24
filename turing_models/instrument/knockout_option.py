import datetime
from dataclasses import dataclass

import numpy as np
from tunny import model
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

    def __post_init__(self):
        self.ctx = ctx
        self.set_param()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 100000
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
        return self.ctx.pricing_date or self._value_date

    @property
    def stock_price_(self) -> float:
        return getattr(self.ctx, f"spot_{self.underlier}") or self._stock_price

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
        return TuringDiscountCurveFlat(
            self.value_date_, self.interest_rate_)

    @property
    def dividend_curve(self) -> TuringDiscountCurveFlat:
        return TuringDiscountCurveFlat(
            self.value_date_, self.dividend_yield_)

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
        return self.model._volatility

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
        p0 = self.price()
        self.stock_price_ += bump
        p_up = self.price()
        self.stock_price_ -= bump
        delta = (p_up - p0) / bump
        return delta

    def eq_gamma(self) -> float:
        p0 = self.price()
        self.stock_price_ -= bump
        p_down = self.price()
        self.stock_price_ += 2*bump
        p_up = self.price()
        self.stock_price_ -= bump
        gamma = (p_up - 2.0 * p0 + p_down) / bump / bump
        return gamma

    def eq_vega(self) -> float:
        p0 = self.price()
        self.v += bump
        p_up = self.price()
        self.v -= bump
        vega = (p_up - p0) / bump
        return vega

    def eq_theta(self) -> float:
        p0 = self.price()
        self.value_date_ = self.value_date_.addDays(1)
        p_up = self.price()
        self.value_date_ = self.value_date_.addDays(-1)
        theta = (p_up - p0) / bump
        return theta

    def eq_rho(self) -> float:
        discount_curve = self.discount_curve
        p0 = self.price()
        self.discount_curve = self.discount_curve.bump(bump)
        p1 = self.price()
        self.discount_curve = discount_curve
        rho = (p1 - p0) / bump
        return rho

    def eq_rho_q(self) -> float:
        dividend_curve = self.dividend_curve
        p0 = self.price()
        self.dividend_curve = self.dividend_curve.bump(bump)
        p1 = self.price()
        self.dividend_curve = dividend_curve
        rho_q = (p1 - p0) / bump
        return rho_q
