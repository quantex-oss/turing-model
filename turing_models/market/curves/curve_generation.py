import datetime
from typing import List

from loguru import logger
import numpy as np
import pandas as pd

from fundamental.turing_db.data import Turing
from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.market.curves import TuringDiscountCurveZeros
from turing_models.market.volatility.fx_vol_surface_vv import TuringFXVolSurfaceVV
from turing_models.market.volatility.fx_vol_surface_plus import TuringFXVolSurfacePlus
from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.calendar import TuringCalendarTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes


class CurveGeneration:
    def __init__(self,
                 annualized_term: list,
                 spot_rate: list,
                 base_date: TuringDate = TuringDate(
                     *(datetime.date.today().timetuple()[:3])),
                 frequency_type: TuringFrequencyTypes = TuringFrequencyTypes.ANNUAL,
                 number_of_days: int = 730):
        self.term = base_date.addYears(annualized_term)
        self.spot_rate = spot_rate
        self.base_date = base_date
        self.frequency_type = frequency_type  # 传入利率的frequency type，默认是年化的
        self.number_of_days = number_of_days  # 默认是两年的自然日：365*2
        self.curve = TuringDiscountCurveZeros(
            self.base_date, self.term, self.spot_rate, self.frequency_type)
        self._generate_nature_day()
        self._generate_nature_day_rate()

    def _generate_nature_day(self):
        """根据base_date和number_of_days生成TuringDate列表"""
        self.nature_days = []
        for i in range(1, self.number_of_days):
            day = self.base_date.addDays(i)
            self.nature_days.append(day)

    def _generate_nature_day_rate(self):
        """根据nature_days生成对应的即期收益率列表"""
        self.nature_days_rate = self.curve.zeroRate(self.nature_days).tolist()

    def get_dates(self):
        return [day.datetime() for day in self.nature_days]

    def get_rates(self):
        return self.nature_days_rate

    def get_data_dict(self):
        nature_days = [day.datetime() for day in self.nature_days]
        return dict(zip(nature_days, self.nature_days_rate))


class FXIRCurve:
    """通过外币隐含利率曲线查询接口获取期限（年）、外币隐含利率和人民币利率，
    进而采用分段三次Hermite插值（PCHIP）方式获取逐日曲线数据"""

    def __init__(self,
                 fx_symbol: (str, CurrencyPair),  # 货币对symbol，例如：'USD/CNY'
                 # 人民币利率曲线类型（'Shibor'、'Shibor3M'、'FR007'）
                 curve_type: (str, RMBIRCurveType) = RMBIRCurveType.Shibor3M,
                 # 即期汇率类型（'central'-中间价、'average'-即期询价报价均值）
                 spot_rate_type: (
                     str, SpotExchangeRateType) = SpotExchangeRateType.Central,
                 base_date: TuringDate = TuringDate(
                     *(datetime.date.today().timetuple()[:3])),
                 number_of_days: int = 730):
        if isinstance(fx_symbol, CurrencyPair):
            self.fx_symbol = fx_symbol.value
        elif isinstance(fx_symbol, str):
            self.fx_symbol = fx_symbol
        else:
            raise TuringError('Please check the input of fx_symbol')

        if isinstance(curve_type, RMBIRCurveType):
            self.curve_type = curve_type.value
        elif isinstance(curve_type, str):
            self.curve_type = curve_type
        else:
            raise TuringError('Please check the input of curve_type')

        if isinstance(spot_rate_type, SpotExchangeRateType):
            self.spot_rate_type = spot_rate_type.value
        elif isinstance(spot_rate_type, str):
            self.spot_rate_type = spot_rate_type
        else:
            raise TuringError('Please check the input of spot_rate_type')

        self.base_date = base_date
        self.number_of_days = number_of_days
        self.fx_asset_id = Turing.get_fx_symbol_to_id(_id=self.fx_symbol)[
            'asset_id']
        self.tenors = None
        self.ccy1_cc_rates = None
        self.ccy2_cc_rates = None
        self._get_iuir_curve_date()
        self._curve_generation()

    def _get_iuir_curve_date(self):
        curves_remote = Turing.get_iuir_curve(asset_ids=[self.fx_asset_id],
                                              curve_type=self.curve_type,
                                              spot_rate_type=self.spot_rate_type)[0].get('iuir_curve_data')
        if curves_remote:
            self.set_property_list(curves_remote, "tenors", "tenor")
            self.set_property_list(
                curves_remote, "ccy1_cc_rates", "implied_interest_rate")
            self.set_property_list(
                curves_remote, "ccy2_cc_rates", "cny_implied_interest_rate")

    def set_property_list(self, curves_date, _property, key):
        _list = []
        for cu in curves_date:
            _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def _curve_generation(self):
        self.ccy1_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy1_cc_rates,
                                              base_date=self.base_date,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)
        self.ccy2_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy2_cc_rates,
                                              base_date=self.base_date,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)

    def get_ccy1_curve(self):
        """获取外币利率曲线的Series"""
        return pd.Series(data=self.ccy1_curve_gen.get_rates(), index=self.ccy1_curve_gen.get_dates())

    def get_ccy2_curve(self):
        """获取人民币利率曲线的Series"""
        return pd.Series(data=self.ccy2_curve_gen.get_rates(), index=self.ccy2_curve_gen.get_dates())


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
            self.tenors = [1/12, 2/12, 0.25, 0.5, 1, 2]

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

        self.volatility_surface = TuringFXVolSurfacePlus(self.base_date,
                                                         self.exchange_rate,
                                                         self.fx_symbol,
                                                         self.fx_symbol[-3:],
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


if __name__ == '__main__':
    fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
                         curve_type=RMBIRCurveType.Shibor3M,
                         spot_rate_type=SpotExchangeRateType.Central)
    print(fx_curve.get_ccy1_curve())
    print(fx_curve.get_ccy2_curve())
    fx_vol_surface = FXOptionImpliedVolatilitySurface(
        fx_symbol=CurrencyPair.USDCNY)
    print(fx_vol_surface.get_vol_surface())
