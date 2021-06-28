from dataclasses import dataclass

import numpy as np

from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.global_types import TuringKnockOutTypes
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme
from turing_models.instrument.equity_option import EqOption


@dataclass
class KnockOutOption(EqOption):

    barrier: float = None
    rebate: float = None
    knock_out_type: str = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 10000
        self.seed = 4242

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
