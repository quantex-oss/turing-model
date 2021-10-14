import datetime
from typing import List, Union

import numpy as np
import pandas as pd
import QuantLib as ql
from loguru import logger

from fundamental.turing_db.data import Turing
from turing_models.instruments.common import CurrencyPair, DiscountCurveType
from turing_models.instruments.common import TuringFXATMMethod, TuringFXDeltaMethod
from turing_models.market.curves.curve_generation import FXIRCurve, ForDiscountCurveGen, DomDiscountCurveGen
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.volatility.fx_vol_surface_ql import FXVolSurface
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.models.model_volatility_fns import TuringVolFunctionTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_types import TuringSolverTypes
from turing_models.utilities.turing_date import TuringDate


class FXOptionImpliedVolatilitySurface:
    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 # 行权价最小值 np.linspace(0.1, 0.9, 17)
                 delta: (list, np.ndarray) = None,
                 tenors: list = None,  # 期限（年化） [1/12, 2/12, 0.25, 0.5, 1, 2]
                 base_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))):

        if isinstance(fx_symbol, CurrencyPair):
            self.fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            self.fx_symbol = fx_symbol
        else:
            raise TuringError('Please check the input of fx_symbol')

        if delta:
            self.delta = delta
        else:
            self.delta = np.linspace(0.1, 0.9, 17)

        if tenors:
            self.tenors = tenors
        else:
            self.tenors = [1 / 12, 2 / 12, 0.25, 0.5, 1, 2]

        self.base_date = base_date
        self.expiry = base_date.addYears(self.tenors)
        self.fx_asset_id = Turing.get_fx_symbol_to_id(_id=self.fx_symbol)[
            'asset_id']
        self.exchange_rate = Turing.get_exchange_rate(
            asset_ids=[self.fx_asset_id])[0]['exchange_rate']

        self.fx_ir_curve = FXIRCurve(self.fx_symbol)
        self.ccy1_curve = self.fx_ir_curve.ccy1_curve_gen.curve  # 外币
        self.ccy2_curve = self.fx_ir_curve.ccy2_curve_gen.curve  # 本币

        self.volatility_types = ["ATM", "25D BF", "25D RR", "10D BF", "10D RR"]
        self.vol_tenors = None
        self.atm_vols = None
        self.butterfly_25delta_vols = None
        self.risk_reversal_25delta_vols = None
        self.butterfly_10delta_vols = None
        self.risk_reversal_10delta_vols = None
        self._get_fx_volatility()

        self.volatility_surface = TuringFXVolSurfaceVV(self.base_date,
                                                       self.exchange_rate,
                                                       self.fx_symbol,
                                                       self.ccy2_curve,
                                                       self.ccy1_curve,
                                                       self.vol_tenors,
                                                       self.atm_vols,
                                                       self.butterfly_25delta_vols,
                                                       self.risk_reversal_25delta_vols,
                                                       self.butterfly_10delta_vols,
                                                       self.risk_reversal_10delta_vols)

    def _get_fx_volatility(self):
        """
            https://yapi.iquantex.com/project/569/interface/api/33713 （外汇期权隐含波动率曲线查询）
            1、请求字段volatility_type为ATM的时候，取返回结果的tenor和volatility，分别拼成独立的列表，依次对应 vol_tenors 和atm_vols
            2、请求字段volatility_type为25D BF的时候，取返回结果的volatility，拼成列表，对应 butterfly_25delta_vols
            3、请求字段volatility_type为25D RR的时候，取返回结果的volatility，拼成列表，对应 risk_reversal_25delta_vols
            4、请求字段volatility_type为10D BF的时候，取返回结果的 volatility，拼成列表，对应 butterfly_10delta_vols
            5、请求字段volatility_type为10D RR的时候，取返回结果的volatility，拼成列表，对应 risk_reversal_10delta_vols
        """
        vol_tenors = []
        atm_vols = []
        butterfly_25delta_vols = []
        risk_reversal_25delta_vols = []
        butterfly_10delta_vols = []
        risk_reversal_10delta_vols = []
        vol_dict = self.fetch_fx_volatility(fx_asset_id=self.fx_asset_id,
                                            volatility_types=self.volatility_types)
        if vol_dict:
            for vol in vol_dict:
                if vol.get("asset_id") == self.fx_asset_id:
                    for x in vol.get("volatility_type_data"):
                        if x.get("volatility_type") == "ATM":
                            for data in x.get("curve_data"):
                                vol_tenors.append(data.get("tenor"))
                                setattr(self, 'vol_tenors', vol_tenors)
                        if x.get("volatility_type") == "ATM":
                            for data in x.get("curve_data"):
                                atm_vols.append(data.get("volatility"))
                                setattr(self, 'atm_vols', atm_vols)
                        if x.get("volatility_type") == "25D BF":
                            for data in x.get("curve_data"):
                                butterfly_25delta_vols.append(
                                    data.get("volatility"))
                                setattr(self, 'butterfly_25delta_vols',
                                        butterfly_25delta_vols)
                        if x.get("volatility_type") == "25D RR":
                            for data in x.get("curve_data"):
                                risk_reversal_25delta_vols.append(
                                    data.get("volatility"))
                                setattr(self, 'risk_reversal_25delta_vols',
                                        risk_reversal_25delta_vols)
                        if x.get("volatility_type") == "10D BF":
                            for data in x.get("curve_data"):
                                butterfly_10delta_vols.append(
                                    data.get("volatility"))
                                setattr(self, 'butterfly_10delta_vols',
                                        butterfly_10delta_vols)
                        if x.get("volatility_type") == "10D RR":
                            for data in x.get("curve_data"):
                                risk_reversal_10delta_vols.append(
                                    data.get("volatility"))
                                setattr(self, 'risk_reversal_10delta_vols',
                                        risk_reversal_10delta_vols)

    @staticmethod
    def fetch_fx_volatility(fx_asset_id=None, volatility_types=None):
        try:
            return Turing.get_volatility_curve(asset_ids=[fx_asset_id],
                                               volatility_type=volatility_types)
        except Exception as e:
            logger.debug(str(e))
            return None

    def get_vol_surface(self):
        """获取波动率曲面的DataFrame"""
        data = {}
        expiry = self.expiry
        tenors = self.tenors
        delta = self.delta
        volatility_surface = self.volatility_surface
        for i in range(len(tenors)):
            ex = expiry[i]
            tenor = tenors[i]
            data[tenor] = []
            for de in delta:
                v = volatility_surface.volatilityFromDeltaDate(de, ex)[0]
                data[tenor].append(v)
        return pd.DataFrame(data, index=delta)


class FXVolSurfaceGen:
    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 currency_pair: Union[str, CurrencyPair],
                 exchange_rate: float,
                 domestic_discount_curve: TuringDiscountCurve = None,
                 foreign_discount_curve: TuringDiscountCurve = None,
                 tenors: List[float] = None,
                 origin_tenors: List[str] = None,
                 atm_vols: List[float] = None,
                 butterfly_25delta_vols: List[float] = None,
                 risk_reversal_25delta_vols: List[float] = None,
                 butterfly_10delta_vols: List[float] = None,
                 risk_reversal_10delta_vols: List[float] = None,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_origin_tenors: List[str] = None,
                 fx_swap_quotes: List[float] = None,
                 shibor_tenors: List[float] = None,
                 shibor_origin_tenors: List[str] = None,
                 shibor_rates: List[float] = None,
                 shibor_swap_tenors: List[float] = None,
                 shibor_swap_origin_tenors: List[str] = None,
                 shibor_swap_rates: [float] = None,
                 volatility_function_type: TuringVolFunctionTypes = TuringVolFunctionTypes.CICC,
                 alpha: float = 1,
                 atm_method: TuringFXATMMethod = TuringFXATMMethod.FWD_DELTA_NEUTRAL,
                 delta_method: TuringFXDeltaMethod = TuringFXDeltaMethod.SPOT_DELTA,
                 solver_type: TuringSolverTypes = TuringSolverTypes.NELDER_MEAD,
                 tol: float = 1e-8):

        if isinstance(value_date, ql.Date):
            self.value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            self.value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            self.value_date_turing = value_date
            self.value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if isinstance(currency_pair, CurrencyPair):
            self.currency_pair = currency_pair.value
        elif isinstance(currency_pair, str):
            if len(currency_pair) != 7:
                raise TuringError("Currency pair must be in ***/***format.")
            self.currency_pair = currency_pair
        else:
            raise TuringError('currency_pair: (str, CurrencyPair)')

        self.exchange_rate = exchange_rate

        self.domestic_discount_curve = domestic_discount_curve
        self.foreign_discount_curve = foreign_discount_curve

        self.tenors = tenors
        self.origin_tenors = origin_tenors
        self.atm_vols = atm_vols
        self.butterfly_25delta_vols = butterfly_25delta_vols
        self.risk_reversal_25delta_vols = risk_reversal_25delta_vols
        self.butterfly_10delta_vols = butterfly_10delta_vols
        self.risk_reversal_10delta_vols = risk_reversal_10delta_vols

        self.fx_swap_tenors = fx_swap_tenors
        self.fx_swap_origin_tenors = fx_swap_origin_tenors
        self.fx_swap_quotes = fx_swap_quotes
        self.shibor_tenors = shibor_tenors
        self.shibor_origin_tenors = shibor_origin_tenors
        self.shibor_rates = shibor_rates
        self.shibor_swap_tenors = shibor_swap_tenors
        self.shibor_swap_origin_tenors = shibor_swap_origin_tenors
        self.shibor_swap_rates = shibor_swap_rates

        self.alpha = alpha
        self.atm_method = atm_method
        self.delta_method = delta_method
        self.volatility_function_type = volatility_function_type
        self.solver_type = solver_type
        self.tol = tol

    @property
    def volatility_surface(self):
        """根据volatility function type区分初始化不同的曲面"""
        if self.volatility_function_type == TuringVolFunctionTypes.VANNA_VOLGA:
            return TuringFXVolSurfaceVV(self.value_date_turing,
                                        self.exchange_rate,
                                        self.currency_pair,
                                        self.domestic_discount_curve,
                                        self.foreign_discount_curve,
                                        self.tenors,
                                        self.atm_vols,
                                        self.butterfly_25delta_vols,
                                        self.risk_reversal_25delta_vols,
                                        self.butterfly_10delta_vols,
                                        self.risk_reversal_10delta_vols,
                                        self.alpha,
                                        self.atm_method,
                                        self.delta_method,
                                        self.volatility_function_type,
                                        self.solver_type,
                                        self.tol)

        elif self.volatility_function_type == TuringVolFunctionTypes.CICC:
            ql.Settings.instance().evaluationDate = self.value_date_ql
            foreign_name = self.currency_pair[0:3]
            domestic_name = self.currency_pair[4:7]
            data_dict = {'Tenor': self.origin_tenors,
                         'ATM': self.atm_vols,
                         '25DRR': self.risk_reversal_25delta_vols,
                         '25DBF': self.butterfly_25delta_vols,
                         '10DRR': self.risk_reversal_10delta_vols,
                         '10DBF': self.butterfly_10delta_vols}
            vol_data = pd.DataFrame(data_dict)
            fore = ForDiscountCurveGen(value_date=self.value_date_ql,
                                       exchange_rate=self.exchange_rate,
                                       fx_swap_tenors=self.fx_swap_tenors,
                                       fx_swap_origin_tenors=self.fx_swap_origin_tenors,
                                       fx_swap_quotes=self.fx_swap_quotes,
                                       shibor_tenors=self.shibor_tenors,
                                       shibor_origin_tenors=self.shibor_origin_tenors,
                                       shibor_rates=self.shibor_rates,
                                       shibor_swap_tenors=self.shibor_swap_tenors,
                                       shibor_swap_origin_tenors=self.shibor_swap_origin_tenors,
                                       shibor_swap_rates=self.shibor_swap_rates,
                                       curve_type=DiscountCurveType.FX_Implied_CICC)
            fwd_crv = fore.fx_forward_curve
            for_crv = fore.discount_curve
            dom = DomDiscountCurveGen(value_date=self.value_date_ql,
                                      shibor_tenors=self.shibor_tenors,
                                      shibor_origin_tenors=self.shibor_origin_tenors,
                                      shibor_rates=self.shibor_rates,
                                      shibor_swap_tenors=self.shibor_swap_tenors,
                                      shibor_swap_origin_tenors=self.shibor_swap_origin_tenors,
                                      shibor_swap_rates=self.shibor_swap_rates,
                                      curve_type=DiscountCurveType.Shibor3M_CICC)
            disc_crv = dom.discount_curve
            calendar = ql.China(ql.China.IB)
            convention = ql.Following
            daycount = ql.Actual365Fixed()
            return FXVolSurface(vol_data,
                                domestic_name,
                                foreign_name,
                                self.exchange_rate,
                                fwd_crv,
                                disc_crv,
                                for_crv,
                                self.value_date_ql,
                                calendar,
                                convention,
                                daycount,
                                True)


if __name__ == '__main__':
    # fx_vol_surface = FXOptionImpliedVolatilitySurface(
    #     fx_symbol=CurrencyPair.USDCNY)
    # print('Volatility Surface\n', fx_vol_surface.get_vol_surface())
    # vol_sur = FXVolSurfaceGen(currency_pair=CurrencyPair.USDCNY).volatility_surface
    strike = 6.6
    expiry = ql.Date(16, 10, 2021)
    # print(vol_sur.interp_vol(expiry, strike))

