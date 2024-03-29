from dataclasses import dataclass

import numpy as np

from turing_models.instruments.eq.equity_option import EqOption
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
    TuringGBMNumericalScheme
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringKnockOutTypes, OptionType
from turing_models.utilities.global_variables import gNumObsInYear, gDaysInYear
from turing_models.utilities.mathematics import N


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class KnockOutOption(EqOption):
    barrier: float = None
    rebate: float = None
    knock_out_type: str = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 1_000_000
        self.days_in_year = gDaysInYear
        self.seed = 4242
        self._check_param()

    def _check_param(self):
        if self.knock_out_type is None:
            if self.option_type is not None:
                rules = {
                    "CALL": TuringKnockOutTypes.UP_AND_OUT_CALL,
                    OptionType.CALL: TuringKnockOutTypes.UP_AND_OUT_CALL,
                    "PUT": TuringKnockOutTypes.DOWN_AND_OUT_PUT,
                    OptionType.PUT: TuringKnockOutTypes.DOWN_AND_OUT_PUT
                }
                self.knock_out_type = rules.get(self.option_type,
                                                TuringError('Please check the input of option_type'))
                if isinstance(self.knock_out_type, TuringError):
                    raise self.knock_out_type

    def price(self) -> float:
        s0 = self.stock_price
        expiry = self.expiry
        start_date = self.start_date
        days_in_year = self.days_in_year
        k = self.strike_price
        b = self.barrier
        r = self.r
        q = self.q
        vol = self.v
        rebate = self.rebate
        notional = self.notional
        texp = self.texp
        knock_out_type = self.knock_out_type
        flag = self.annualized_flag
        participation_rate = self.participation_rate
        num_ann_obs = self.num_ann_obs

        if texp < 0:
            raise TuringError("Option expires before value date.")

        ln_s0k = np.log(s0 / k)
        sqrt_t = np.sqrt(texp)

        sigma_root_t = vol * sqrt_t
        v2 = vol * vol
        mu = r - q
        d1 = (ln_s0k + (mu + v2 / 2.0) * texp) / sigma_root_t
        d2 = (ln_s0k + (mu - v2 / 2.0) * texp) / sigma_root_t
        df = np.exp(-r * texp)
        dq = np.exp(-q * texp)

        c = s0 * dq * N(d1) - k * df * N(d2)
        p = k * df * N(-d2) - s0 * dq * N(-d1)

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL and s0 >= b:
            return rebate * notional * np.exp(- r * texp)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT and s0 <= b:
            return rebate * notional * np.exp(- r * texp)

        num_obs = 1 + texp * num_ann_obs

        # Correction by Broadie, Glasserman and Kou, Mathematical Finance, 1997
        # Adjusts the barrier for discrete and not continuous observations
        t = texp / num_obs

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            h_adj = b * np.exp(0.5826 * vol * np.sqrt(t))
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            h_adj = b * np.exp(-0.5826 * vol * np.sqrt(t))
        else:
            raise TuringError("Unknown barrier option type." +
                              str(knock_out_type))

        b = h_adj

        l = (mu + v2 / 2.0) / v2
        y = np.log(b * b / (s0 * k)) / sigma_root_t + l * sigma_root_t
        x1 = np.log(s0 / b) / sigma_root_t + l * sigma_root_t
        y1 = np.log(b / s0) / sigma_root_t + l * sigma_root_t
        h_over_s = b / s0

        whole_term = (expiry - start_date) / days_in_year

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            if b > k:
                c_ui = s0 * dq * N(x1) - k * df * N(x1 - sigma_root_t) \
                    - s0 * dq * pow(h_over_s, 2.0 * l) * (N(-y) - N(-y1)) \
                    + k * df * pow(h_over_s, 2.0 * l - 2.0) * \
                    (N(-y + sigma_root_t) - N(-y1 + sigma_root_t))
                price = participation_rate * (c - c_ui) + rebate * whole_term ** flag * s0 * df * (
                    1 - N(sigma_root_t - x1) + pow(h_over_s, 2.0 * l - 2.0) * N(-y1 + sigma_root_t))
            else:
                price = rebate * whole_term ** flag * s0 * df * (
                    1 - N(sigma_root_t - x1) + pow(h_over_s, 2.0 * l - 2.0) * N(-y1 + sigma_root_t))

        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            if b >= k:
                price = rebate * whole_term ** flag * s0 * df * (
                    1 - N(x1 - sigma_root_t) + pow(h_over_s, 2.0 * l - 2.0) * N(y1 - sigma_root_t))
            else:
                p_di = -s0 * dq * N(-x1) \
                    + k * df * N(-x1 + sigma_root_t) \
                    + s0 * dq * pow(h_over_s, 2.0 * l) * (N(y) - N(y1)) \
                       - k * df * pow(h_over_s, 2.0 * l - 2.0) * \
                    (N(y - sigma_root_t) - N(y1 - sigma_root_t))
                price = participation_rate * (p - p_di) + rebate * whole_term ** flag * s0 * df * (
                    1 - N(x1 - sigma_root_t) + pow(h_over_s, 2.0 * l - 2.0) * N(y1 - sigma_root_t))
        else:
            raise TuringError("Unknown barrier option type." +
                              str(knock_out_type))

        v = price * notional / s0
        return v

    def price_mc(self) -> float:
        s0 = self.stock_price
        k = self.strike_price
        b = self.barrier
        r = self.r
        q = self.q
        vol = self.v
        rebate = self.rebate
        notional = self.notional
        texp = self.texp
        knock_out_type = self.knock_out_type
        flag = self.annualized_flag
        participation_rate = self.participation_rate
        num_ann_obs = self.num_ann_obs
        num_paths = self.num_paths
        seed = self.seed

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL and s0 >= b:
            return rebate * texp ** flag * notional * np.exp(-r * texp)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT and s0 <= b:
            return rebate * texp ** flag * notional * np.exp(-r * texp)

        process = TuringProcessSimulator()
        process_type = TuringProcessTypes.GBM
        scheme = TuringGBMNumericalScheme.ANTITHETIC
        model_params = (s0, r - q, vol, scheme)

        Sall = process.getProcess(process_type, texp, model_params,
                                  num_ann_obs, num_paths, seed)

        (num_paths, _) = Sall.shape

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            barrier_crossed_from_below = [False] * num_paths
            for p in range(0, num_paths):
                barrier_crossed_from_below[p] = np.any(Sall[p] >= b)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            barrier_crossed_from_above = [False] * num_paths
            for p in range(0, num_paths):
                barrier_crossed_from_above[p] = np.any(Sall[p] <= b)

        payoff = np.zeros(num_paths)
        ones = np.ones(num_paths)

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            payoff = np.maximum((Sall[:, -1] - k) / s0, 0.0) * \
                participation_rate * (ones - barrier_crossed_from_below) + \
                rebate * texp ** flag * (ones * barrier_crossed_from_below)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            payoff = np.maximum((k - Sall[:, -1]) / s0, 0.0) * \
                participation_rate * (ones - barrier_crossed_from_above) + \
                rebate * texp ** flag * (ones * barrier_crossed_from_above)

        return payoff.mean() * np.exp(- r * texp) * notional

    def _resolve(self):
        super()._resolve()
        if self.product_type is None:
            setattr(self, 'product_type', 'KNOCK_OUT')
        self.__post_init__()

    def __repr__(self):
        s = super().__repr__()
        s += f'''
Barrier: {self.barrier}
Rebate: {self.rebate}'''
        return s
