from dataclasses import dataclass, field
from typing import List, Any

import numpy as np

from fundamental.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.gbm_process import TuringGBMProcess
from turing_models.instruments.snowball_option import SnowballOption
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BasketSnowballOption(SnowballOption):

    untriggered_rebate: float = None
    business_day_adjust_type: str = None
    correlation_matrix: np.ndarray = None
    weights: List[Any] = field(default_factory=list)
    __value_date = None
    __stock_price = None
    __volatility = None
    __discount_curve = None
    __dividend_curve = None

    def __post_init__(self):
        super().__post_init__()

    def set_param(self):
        super().set_param()
        if self.underlier:
            self.num_assets = len(self.underlier)

    @property
    def stock_price_(self) -> np.ndarray:
        if self.__stock_price:
            return self.__stock_price

        # self.underlier是一个列表
        for i in range(len(self.underlier)):
            spot = getattr(self.ctx, f"spot_{self.underlier[i]}")
            if spot:
                self._stock_price[i] = spot

        return np.array(self._stock_price)

    @stock_price_.setter
    def stock_price_(self, value: np.ndarray):
        self.__stock_price = value

    @property
    def volatility_(self) -> np.ndarray:
        if self.__volatility:
            return self.__volatility

        # self.underlier是一个列表
        for i in range(len(self.underlier)):
            vol = getattr(self.ctx, f"volatility_{self.underlier[i]}")
            if vol:
                self._volatility[i] = vol

        return np.array(self._volatility)

    @volatility_.setter
    def volatility_(self, value: np.ndarray):
        self.__volatility = value

    @property
    def dividend_curve(self) -> List[TuringDiscountCurveFlat]:
        if self.__dividend_curve:
            return self.__dividend_curve
        else:
            curve_list = []
            for dividend_yield in self.dividend_yield_:
                curve = TuringDiscountCurveFlat(
                    self.value_date_, dividend_yield)
                curve_list.append(curve)
            return curve_list

    @dividend_curve.setter
    def dividend_curve(self, value: List[TuringDiscountCurveFlat]):
        self.__dividend_curve = value

    @property
    def q(self) -> np.ndarray:
        if self.expiry >= self.value_date_:
            q_list = []
            for curve in self.dividend_curve:
                dq = curve.df(self.expiry)
                q = -np.log(dq) / self.texp
                q_list.append(q)
            return np.array(q_list)
        else:
            raise TuringError("Expiry must be > Value_Date")

    def price(self) -> float:
        s0 = self.stock_price_
        r = self.r
        q = self.q
        vol = self.volatility_
        texp = self.texp
        num_ann_obs = self.num_ann_obs
        num_paths = self.num_paths
        num_assets = self.num_assets
        num_time_steps = int(num_ann_obs * texp)
        corr_matrix = self.correlation_matrix
        weights = self.weights
        seed = self.seed
        mus = r - q

        self._validate(s0,
                       q,
                       vol,
                       corr_matrix,
                       weights)

        process = TuringGBMProcess()

        sall = process.getPathsAssets(num_assets,
                                      num_paths,
                                      num_time_steps,
                                      texp,
                                      mus,
                                      s0,
                                      vol,
                                      corr_matrix,
                                      seed)
        (num_paths, num_time_steps, _) = sall.shape
        sall_bskt = np.matmul(sall, weights)
        s0_dot = np.dot(s0, weights)
        return self._payoff(s0_dot, sall_bskt, num_paths, num_time_steps)

    # def price_new(self) -> float:
    #     s0 = self.stock_price_
    #     k1 = self.barrier
    #     k2 = self.knock_in_price
    #     sk1 = self.knock_in_strike1
    #     sk2 = self.knock_in_strike2
    #     start_date = self.start_date
    #     expiry = self.expiry
    #     value_date = self.value_date_
    #     r = self.r
    #     q = self.q
    #     vol = self.volatility_
    #     rebate = self.rebate
    #     notional = self.notional
    #     texp = self.texp
    #     option_type = self.option_type_
    #     knock_in_type = self.knock_in_type_
    #     flag = self.annualized_flag
    #     participation_rate = self.participation_rate
    #     num_ann_obs = self.num_ann_obs
    #     num_paths = self.num_paths
    #     seed = self.seed
    #
    #     schedule_monthly = TuringSchedule(start_date,
    #                                       expiry,
    #                                       freqType=TuringFrequencyTypes.MONTHLY,
    #                                       calendarType=TuringCalendarTypes.CHINA_SSE)
    #     knock_out_obs_days = schedule_monthly._adjustedDates
    #
    #     schedule_daily = TuringSchedule(value_date,
    #                                     expiry,
    #                                     freqType=TuringFrequencyTypes.DAILY,
    #                                     calendarType=TuringCalendarTypes.CHINA_SSE)
    #     bus_days = schedule_daily._adjustedDates
    #
    #     np.random.seed(seed)
    #     mu = r - q
    #     v2 = vol ** 2
    #     n = int(expiry - value_date)
    #     dt = 1 / gDaysInYear
    #     date_list = [value_date]
    #     for i in range(1, n + 1):
    #         dateinc = value_date.addDays(i)
    #         date_list.append(dateinc)

    def _validate(self,
                  stock_prices,
                  dividend_yields,
                  volatilities,
                  correlations,
                  weights):

        num_assets = self.num_assets
        if len(stock_prices) != num_assets:
            raise TuringError(
                "Stock prices must have a length " + str(num_assets))

        if len(dividend_yields) != num_assets:
            raise TuringError(
                "Dividend yields must have a length " + str(num_assets))

        if len(volatilities) != num_assets:
            raise TuringError(
                "Volatilities must have a length " + str(num_assets))

        if len(weights) != num_assets:
            raise TuringError(
                "Weights must have a length " + str(num_assets))

        if np.sum(weights) != 1:
            raise TuringError(
                "Weights must sums to one ")

        if correlations.ndim != 2:
            raise TuringError(
                "Correlation must be a 2D matrix ")

        if correlations.shape[0] != num_assets:
            raise TuringError(
                "Correlation cols must have a length " + str(num_assets))

        if correlations.shape[1] != num_assets:
            raise TuringError(
                "correlation rows must have a length " + str(num_assets))

        for i in range(0, num_assets):
            if correlations[i, i] != 1.0:
                raise TuringError("Corr matrix must have 1.0 on the diagonal")

            for j in range(0, i):
                if abs(correlations[i, j]) > 1.0:
                    raise TuringError("Correlations must be [-1, +1]")

                if abs(correlations[j, i]) > 1.0:
                    raise TuringError("Correlations must be [-1, +1]")

                if correlations[i, j] != correlations[j, i]:
                    raise TuringError("Correlation matrix must be symmetric")

    def __repr__(self):
        s = super().__repr__()
        s += to_string("Untriggered Rebate", self.untriggered_rebate)
        s += to_string("Business Day Adjust Type", self.business_day_adjust_type)
        return s
