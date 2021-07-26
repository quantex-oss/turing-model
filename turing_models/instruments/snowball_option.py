from dataclasses import dataclass
from typing import Union

import numpy as np

from turing_models.utilities.global_variables import gNumObsInYear
from turing_models.utilities.global_types import TuringOptionTypes, \
     TuringKnockInTypes, TuringOptionType
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
     TuringGBMNumericalScheme
from turing_models.instruments.equity_option import EqOption
from turing_models.utilities.helper_functions import to_string


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class SnowballOption(EqOption):

    barrier: float = None
    rebate: float = None
    coupon: float = None
    knock_in_price: float = None
    knock_in_type: Union[str, TuringKnockInTypes] = None
    knock_in_strike1: float = None
    knock_in_strike2: float = None

    def __post_init__(self):
        super().__post_init__()
        self.num_ann_obs = gNumObsInYear
        self.num_paths = 10000
        self.seed = 4242

    @property
    def option_type_(self) -> TuringOptionTypes:
        if self.option_type == "CALL" or self.option_type == TuringOptionType.CALL:
            return TuringOptionTypes.SNOWBALL_CALL
        elif self.option_type == "PUT" or self.option_type == TuringOptionType.PUT:
            return TuringOptionTypes.SNOWBALL_PUT
        else:
            raise Exception('Please check the input of option_type')

    @property
    def knock_in_type_(self) -> TuringKnockInTypes:
        if isinstance(self.knock_in_type, TuringKnockInTypes):
            return self.knock_in_type
        else:
            if self.knock_in_type == 'return':
                return TuringKnockInTypes.RETURN
            elif self.knock_in_type == 'vanilla':
                return TuringKnockInTypes.VANILLA
            else:
                return TuringKnockInTypes.SPREADS

    def price(self) -> float:
        s0 = self.stock_price_
        k1 = self.barrier
        k2 = self.knock_in_price
        sk1 = self.knock_in_strike1
        sk2 = self.knock_in_strike2
        expiry = self.expiry
        value_date = self.value_date_
        r = self.r
        q = self.q
        vol = self.v
        rebate = self.rebate
        notional = self.notional
        texp = self.texp
        option_type = self.option_type_
        knock_in_type = self.knock_in_type_
        flag = self.annualized_flag
        participation_rate = self.participation_rate
        num_ann_obs = self.num_ann_obs
        num_paths = self.num_paths
        seed = self.seed

        process = TuringProcessSimulator()
        process_type = TuringProcessTypes.GBM
        scheme = TuringGBMNumericalScheme.ANTITHETIC
        model_params = (s0, r-q, vol, scheme)

        Sall = process.getProcess(process_type, texp, model_params,
                                  num_ann_obs, num_paths, seed)

        (num_paths, num_time_steps) = Sall.shape

        out_call_sign = [False] * num_paths
        out_call_index = [False] * num_paths
        in_call_sign = [False] * num_paths
        out_put_sign = [False] * num_paths
        out_put_index = [False] * num_paths
        in_put_sign = [False] * num_paths

        # 相邻敲出观察日之间的交易日数量
        num_bus_days = int(num_ann_obs / 12)

        # 生成一个标识索引的列表
        slice_length = (expiry._y - value_date._y) * 12 + \
                       (expiry._m - value_date._m) + \
                       (expiry._d > value_date._d)
        index_list = list(range(num_time_steps))[::-num_bus_days][:slice_length][::-1]

        if option_type == TuringOptionTypes.SNOWBALL_CALL:
            for p in range(0, num_paths):
                out_call_sign[p] = np.any(Sall[p][::-num_bus_days][:slice_length] >= k1)

                if out_call_sign[p]:
                    for i in index_list:
                        if Sall[p][i] >= k1:
                            out_call_index[p] = i
                            break

                in_call_sign[p] = np.any(Sall[p] < k2)

        elif option_type == TuringOptionTypes.SNOWBALL_PUT:
            for p in range(0, num_paths):
                out_put_sign[p] = np.any(Sall[p][::-num_bus_days][:slice_length] <= k1)

                if out_put_sign[p]:
                    for i in index_list:
                        if Sall[p][i] <= k1:
                            out_put_index[p] = i
                            break

                in_put_sign[p] = np.any(Sall[p] > k2)

        ones = np.ones(num_paths)
        # list转成ndarray
        out_call_sign = np.array(out_call_sign)
        not_out_call_sign = ones - out_call_sign
        out_call_index = np.array(out_call_index)
        in_call_sign = np.array(in_call_sign)
        not_in_call_sign = ones - in_call_sign
        out_put_sign = np.array(out_put_sign)
        not_out_put_sign = ones - out_put_sign
        out_put_index = np.array(out_put_index)
        in_put_sign = np.array(in_put_sign)
        not_in_put_sign = ones - in_put_sign

        if option_type == TuringOptionTypes.SNOWBALL_CALL:

            payoff = out_call_sign * ((notional * rebate * (out_call_index / num_ann_obs)**flag) *
                     np.exp(-r * out_call_index / num_ann_obs)) + not_out_call_sign * not_in_call_sign * \
                     ((notional * rebate * texp**flag) * np.exp(-r * texp))

            if knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_call_sign * in_call_sign * \
                          (-notional * (1 - Sall[:, -1] / s0) *
                           participation_rate * np.exp(-r * texp))

            elif knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_call_sign * in_call_sign * \
                          (-notional * np.maximum(sk1 - Sall[:, -1] / s0, 0) * \
                           participation_rate * texp**flag * np.exp(-r * texp))

            elif knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_call_sign * in_call_sign * \
                          (-notional * np.maximum(sk1 - np.maximum(Sall[:, -1] / s0, sk2), 0) * \
                           participation_rate * texp**flag * np.exp(-r * texp))

        elif option_type == TuringOptionTypes.SNOWBALL_PUT:

            payoff = out_put_sign * ((notional * rebate * (out_put_index / num_ann_obs)**flag) *
                     np.exp(-r * out_put_index / num_ann_obs)) + not_out_put_sign * not_in_put_sign * \
                     ((notional * rebate * texp**flag) * np.exp(-r * texp))

            if knock_in_type == TuringKnockInTypes.RETURN:
                payoff += not_out_put_sign * in_put_sign * \
                          (-notional * (Sall[:, -1] / s0 - 1) * \
                           participation_rate * np.exp(-r * texp))

            elif knock_in_type == TuringKnockInTypes.VANILLA:
                payoff += not_out_put_sign * in_put_sign * \
                          (-notional * np.maximum(Sall[:, -1] / s0 - sk1, 0) * \
                           participation_rate * texp**flag * np.exp(-r * texp))

            elif knock_in_type == TuringKnockInTypes.SPREADS:
                payoff += not_out_put_sign * in_put_sign * \
                          (-notional * np.maximum(np.minimum(Sall[:, -1] / s0, sk2) - sk1, 0) * \
                           participation_rate * texp**flag * np.exp(-r * texp))

        return payoff.mean()

    def __repr__(self):
        s = super().__repr__()
        s += to_string("Barrier", self.barrier)
        s += to_string("Rebate", self.rebate)
        s += to_string("Coupon", self.coupon)
        s += to_string("Knock In Price", self.knock_in_price)
        s += to_string("Knock In Type", self.knock_in_type)
        s += to_string("Knock In Strike1", self.knock_in_strike1)
        s += to_string("Knock In Strike2", self.knock_in_strike2)
        return s
