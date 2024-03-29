from dataclasses import dataclass, field
from typing import List, Any

import numpy as np

from turing_models.market.curves.discount_curve_flat import TuringDiscountCurveFlat
from turing_models.models.gbm_process import TuringGBMProcess
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.models.process_simulator import TuringProcessSimulator, TuringProcessTypes, \
    TuringGBMNumericalScheme
from turing_models.instruments.eq.snowball_option import SnowballOption
from turing_models.utilities.helper_functions import to_string, to_turing_date
from turing_models.utilities.error import TuringError


@dataclass(repr=False, eq=False, order=False, unsafe_hash=True)
class BasketSnowballOption(SnowballOption):

    correlation_matrix: np.ndarray = None
    weights: List[Any] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

    @property
    def q(self) -> np.ndarray:
        value_date = self.transformed_value_date
        if self.expiry > value_date:
            return np.array([curve.zeroRate(self.expiry) for curve in self.dividend_curve])
        else:
            raise TuringError("Expiry must be > Value_Date")

    def price_3dim(self) -> float:
        s0 = np.array(self.stock_price)
        r = self.r
        q = self.q
        vol = self.volatility
        texp = self.texp
        num_paths = self.num_paths
        num_assets = self.num_assets
        corr_matrix = self.correlation_matrix
        weights = self.weights
        mus = r - q

        seed = self.seed

        # 减一是为了适配getPathsAssets函数
        num_time_steps = len(self.bus_days) - 1

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

        return self._payoff(sall_bskt, num_paths)

    def price(self) -> float:
        s0 = np.array(self.stock_price)
        r = self.r
        q = self.q
        vol = self.volatility
        texp = self.texp
        num_paths = self.num_paths
        num_assets = self.num_assets
        corr_matrix = self.correlation_matrix
        weights = self.weights
        num_ann_obs = self.num_ann_obs

        process = TuringProcessSimulator()
        process_type = TuringProcessTypes.GBM
        scheme = TuringGBMNumericalScheme.ANTITHETIC

        # 减一是为了适配getGBMPaths函数
        num_time_steps = len(self.bus_days) - 1

        seed = self.seed

        self._validate(s0,
                       q,
                       vol,
                       corr_matrix,
                       weights)

        smean = 0.0
        for ia in range(0, num_assets):
            smean = smean + s0[ia] * weights[ia]

        # Moment matching - starting with dividend
        qnum = 0.0
        qden = 0.0
        for ia in range(0, self.num_assets):
            qnum = qnum + weights[ia] * s0[ia] * np.exp(-q[ia] * texp)
            qden = qden + weights[ia] * s0[ia]
        qhat = -np.log(qnum / qden) / texp

        # Moment matching - matching volatility
        vnum = 0.0
        for ia in range(0, self.num_assets):
            for ja in range(0, ia):
                rhoSigmaSigma = vol[ia] * vol[ja] * corr_matrix[ia, ja]
                expTerm = (q[ia] + q[ja] - rhoSigmaSigma) * texp
                vnum = vnum + weights[ia] * weights[ja] * \
                    s0[ia] * s0[ja] * np.exp(-expTerm)

        vnum *= 2.0

        for ia in range(0, self.num_assets):
            rhoSigmaSigma = vol[ia] ** 2
            expTerm = (2.0 * q[ia] - rhoSigmaSigma) * texp
            vnum = vnum + ((weights[ia] * s0[ia]) ** 2) * np.exp(-expTerm)

        vhat2 = np.log(vnum / qnum / qnum) / texp

        # den = np.sqrt(vhat2) * sqrtT
        mu = r - qhat
        model_params = (smean, mu, np.sqrt(vhat2), scheme)

        Sall = process.getProcess(process_type, texp, model_params,
                                  num_ann_obs, num_paths, seed, num_time_steps)

        (num_paths, _) = Sall.shape

        return self._payoff(Sall, num_paths)

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
        s += to_string("Business Day Adjust Type",
                       self.business_day_adjust_type)
        return s
