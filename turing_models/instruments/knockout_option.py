from dataclasses import dataclass
from typing import Union

import numpy as np

from fundamental.turing_db.option_data import OptionApi
from turing_models.instruments.equity_option import EqOption
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
    TuringGBMNumericalScheme
from turing_models.utilities.global_types import TuringKnockOutTypes
from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.helper_functions import to_string
from turing_models.utilities.mathematics import N


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class KnockOutOption(EqOption):
    barrier: float = None
    rebate: float = None
    knock_out_type: Union[str, TuringKnockOutTypes] = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 10000
        self.seed = 4242

    @property
    def knock_out_type_(self) -> TuringKnockOutTypes:
        if isinstance(self.knock_out_type, TuringKnockOutTypes):
            return self.knock_out_type
        else:
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

        if texp < 0:
            raise Exception("Option expires before value date.")

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
            raise Exception("Unknown barrier option type." +
                            str(knock_out_type))

        b = h_adj

        l = (mu + v2 / 2.0) / v2
        y = np.log(b * b / (s0 * k)) / sigma_root_t + l * sigma_root_t
        x1 = np.log(s0 / b) / sigma_root_t + l * sigma_root_t
        y1 = np.log(b / s0) / sigma_root_t + l * sigma_root_t
        h_over_s = b / s0

        if knock_out_type == TuringKnockOutTypes.UP_AND_OUT_CALL:
            if b > k:
                c_ui = s0 * dq * N(x1) - k * df * N(x1 - sigma_root_t) \
                       - s0 * dq * pow(h_over_s, 2.0 * l) * (N(-y) - N(-y1)) \
                       + k * df * pow(h_over_s, 2.0 * l - 2.0) * (N(-y + sigma_root_t) - N(-y1 + sigma_root_t))
                price = participation_rate * (c - c_ui) + rebate * texp ** flag * s0 * df * (
                        1 - N(sigma_root_t - x1) + pow(h_over_s, 2.0 * l - 2.0) * N(-y1 + sigma_root_t))
            else:
                price = rebate * texp ** flag * s0 * df * (
                        1 - N(sigma_root_t - x1) + pow(h_over_s, 2.0 * l - 2.0) * N(-y1 + sigma_root_t))

        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            if b >= k:
                price = rebate * texp ** flag * s0 * df * (
                        1 - N(x1 - sigma_root_t) + pow(h_over_s, 2.0 * l - 2.0) * N(y1 - sigma_root_t))
            else:
                p_di = -s0 * dq * N(-x1) \
                       + k * df * N(-x1 + sigma_root_t) \
                       + s0 * dq * pow(h_over_s, 2.0 * l) * (N(y) - N(y1)) \
                       - k * df * pow(h_over_s, 2.0 * l - 2.0) * (N(y - sigma_root_t) - N(y1 - sigma_root_t))
                price = participation_rate * (p - p_di) + rebate * texp ** flag * s0 * df * (
                        1 - N(x1 - sigma_root_t) + pow(h_over_s, 2.0 * l - 2.0) * N(y1 - sigma_root_t))
        else:
            raise Exception("Unknown barrier option type." +
                            str(knock_out_type))

        v = price * notional / s0
        return v

    def price_mc(self) -> float:
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
                     rebate * texp ** flag * (ones * barrierCrossedFromBelow)
        elif knock_out_type == TuringKnockOutTypes.DOWN_AND_OUT_PUT:
            payoff = np.maximum((k - Sall[:, -1]) / s0, 0.0) * \
                     participation_rate * (ones - barrierCrossedFromAbove) + \
                     rebate * texp ** flag * (ones * barrierCrossedFromAbove)

        return payoff.mean() * np.exp(- r * texp) * notional

    def option_resolve(self):
        if self.asset_id and not self.asset_id.startswith("OPTION_"+self.__class__.__name__):
            temp_dict = OptionApi.fetch_Option(asset_id=self.asset_id)
            for k, v in temp_dict.items():
                if not getattr(self, k, None) and v:
                    setattr(self, k, v)
        if self.underlier:
            if not self.stock_price_:
                setattr(self, "stock_price", OptionApi.stock_price(underlier=self.underlier))
        if self.value_date_ and self.underlier:
            if not self.interest_rate and not self.zero_dates and not self.zero_rates:
                zero_dates, zero_rates = OptionApi.fill_r()
                setattr(self, "zero_dates", zero_dates)
                setattr(self, "zero_rates", zero_rates)
            if not self.volatility_:
                get_volatility = OptionApi.get_volatility(self.value_date_, self.underlier)
                if get_volatility:
                    setattr(self, 'volatility', get_volatility)

    def __repr__(self):
        s = super().__repr__()
        s += to_string("Barrier", self.barrier)
        s += to_string("Rebate", self.rebate)
        s += to_string("Knock Out Type", self.knock_out_type)
        return s
