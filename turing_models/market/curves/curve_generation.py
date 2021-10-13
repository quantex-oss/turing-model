import datetime
from typing import List, Union

import pandas as pd
import QuantLib as ql

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType, DiscountCurveType
from turing_models.instruments.rates.irs import create_ibor_single_curve
from turing_models.market.curves.curve_cicc import Shibor3M, FXImpliedAssetCurve, FXForwardCurve
from turing_models.market.curves.discount_curve import TuringDiscountCurve
from turing_models.market.curves.discount_curve_fx_implied import TuringDiscountCurveFXImplied
from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities.day_count import TuringDayCountTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.global_types import TuringSwapTypes
from turing_models.utilities.turing_date import TuringDate


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


class DomDiscountCurveGen:
    """生成本币折现曲线"""

    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 shibor_tenors: List[float] = None,
                 shibor_origin_tenors: List[str] = None,
                 shibor_rates: List[float] = None,
                 shibor_swap_tenors: List[float] = None,
                 shibor_swap_origin_tenors: List[str] = None,
                 shibor_swap_rates: [float] = None,
                 curve_type: DiscountCurveType = DiscountCurveType.Shibor3M_CICC):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if curve_type == DiscountCurveType.Shibor3M:
            shibor_deposit_tenors = shibor_tenors[:5]
            shibor_deposit_rates = shibor_rates[:5]

            self.tenors = shibor_deposit_tenors + shibor_swap_tenors
            # 转成TuringDate格式
            self.dates = value_date_turing.addYears(self.tenors)
            self.dom_curve = create_ibor_single_curve(value_date_turing,
                                                      shibor_deposit_tenors,
                                                      shibor_deposit_rates,
                                                      TuringDayCountTypes.ACT_365F,
                                                      shibor_swap_tenors,
                                                      TuringSwapTypes.PAY,
                                                      shibor_swap_rates,
                                                      TuringFrequencyTypes.QUARTERLY,
                                                      TuringDayCountTypes.ACT_365F, 0)
        elif curve_type == DiscountCurveType.Shibor3M_CICC:
            ql.Settings.instance().evaluationDate = value_date_ql
            shibor_deposit_origin_tenors = shibor_origin_tenors[:5]
            shibor_deposit_origin_tenors[0] = '1D'  # 把'O/N'转换成'1D'，ql不支持'O/N'
            shibor_deposit_rates = shibor_rates[:5]
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            shibor_deposit_mkt_data = pd.DataFrame(data=shibor_deposit_rates, index=shibor_deposit_origin_tenors).T

            shibor_swap_mkt_data = pd.DataFrame(data=shibor_swap_rates, index=shibor_swap_origin_tenors).T

            # TODO: 待与中金同事确认后改为从外部传入的格式
            date1 = '2019-07-05'
            date2 = '2019-07-08'
            date3 = '2019-07-09'
            rate1 = TuringDB.shibor_curve(date=TuringDate.fromString(date1, '%Y-%m-%d'))['rate'][4]
            rate2 = TuringDB.shibor_curve(date=TuringDate.fromString(date2, '%Y-%m-%d'))['rate'][4]
            rate3 = TuringDB.shibor_curve(date=TuringDate.fromString(date3, '%Y-%m-%d'))['rate'][4]
            fixing_data = pd.DataFrame(data={'日期': [date1, date2, date3], 'Fixing': [rate1, rate2, rate3]})

            self.dom_curve = Shibor3M(shibor_deposit_mkt_data, shibor_swap_mkt_data, fixing_data, value_date_ql).curve

    @property
    def discount_curve(self):
        return self.dom_curve


class ForDiscountCurveGen:
    """生成外币折现曲线"""

    def __init__(self,
                 value_date: Union[TuringDate, ql.Date],
                 exchange_rate: float,
                 fx_swap_tenors: List[float] = None,
                 fx_swap_origin_tenors: List[str] = None,
                 fx_swap_quotes: List[float] = None,
                 shibor_tenors: List[float] = None,
                 shibor_origin_tenors: List[str] = None,
                 shibor_rates: List[float] = None,
                 shibor_swap_tenors: List[float] = None,
                 shibor_swap_origin_tenors: List[str] = None,
                 shibor_swap_rates: [float] = None,
                 curve_type: DiscountCurveType = DiscountCurveType.FX_Implied_CICC):
        if isinstance(value_date, ql.Date):
            value_date_turing = TuringDate(value_date.year(), value_date.month(), value_date.dayOfMonth())
            value_date_ql = value_date
        elif isinstance(value_date, TuringDate):
            value_date_turing = value_date
            value_date_ql = ql.Date(value_date._d, value_date._m, value_date._y)
        else:
            raise TuringError('value_date: (TuringDate, ql.Date)')

        if curve_type == DiscountCurveType.FX_Implied:
            dom_discount_curve_gen = DomDiscountCurveGen(value_date_turing, curve_type=DiscountCurveType.Shibor3M)
            domestic_discount_curve = dom_discount_curve_gen.discount_curve
            _tenors = dom_discount_curve_gen.tenors
            dates = value_date_turing.addYears(_tenors)
            future_dates = value_date_turing.addYears(fx_swap_tenors)
            fwd_dfs = []
            for quote in fx_swap_quotes:
                fwd_dfs.append(exchange_rate / (exchange_rate + quote))
            fx_forward_curve = TuringDiscountCurve(value_date_turing, future_dates, fwd_dfs)
            self.for_curve = TuringDiscountCurveFXImplied(value_date_turing,
                                                          dates,
                                                          domestic_discount_curve,
                                                          fx_forward_curve)
        elif curve_type == DiscountCurveType.FX_Implied_CICC:
            ql.Settings.instance().evaluationDate = value_date_ql
            dom_discount_curve_gen = DomDiscountCurveGen(value_date=value_date_ql,
                                                         shibor_tenors=shibor_tenors,
                                                         shibor_origin_tenors=shibor_origin_tenors,
                                                         shibor_rates=shibor_rates,
                                                         shibor_swap_tenors=shibor_swap_tenors,
                                                         shibor_swap_origin_tenors=shibor_swap_origin_tenors,
                                                         shibor_swap_rates=shibor_swap_rates,
                                                         curve_type=DiscountCurveType.Shibor3M_CICC)
            domestic_discount_curve = dom_discount_curve_gen.discount_curve
            fx_swap_origin_tenors[0: 3] = ['1D', '2D', '3D']  # 把ON', 'TN', 'SN'转换成'1D', '2D', '3D'，ql不支持ON', 'TN', 'SN'
            # 与中金现在的模型代码兼容，故拼成同格式的DataFrame
            data_dict = {'Tenor': fx_swap_origin_tenors, 'Spread': fx_swap_quotes}
            fwd_data = pd.DataFrame(data=data_dict)
            # TODO: 去掉硬编码
            self.fx_forward_curve = FXForwardCurve(exchange_rate,
                                                   fwd_data,
                                                   value_date_ql,
                                                   ql.UnitedStates(),
                                                   ql.Actual365Fixed()).curve
            self.for_curve = FXImpliedAssetCurve(domestic_discount_curve,
                                                 self.fx_forward_curve,
                                                 value_date_ql,
                                                 ql.UnitedStates(),
                                                 ql.Actual365Fixed()).curve

    @property
    def discount_curve(self):
        return self.for_curve


if __name__ == '__main__':
    # fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
    #                      curve_type=RMBIRCurveType.Shibor3M,
    #                      spot_rate_type=SpotExchangeRateType.Central)
    # print('CCY1 Curve\n', fx_curve.get_ccy1_curve())
    # print('CCY2 Curve\n', fx_curve.get_ccy2_curve())
    # dom = DomDiscountCurveGen()
    daycount = ql.Actual365Fixed()
    expiry = ql.Date(16, 10, 2021)
    # print(dom.discount_curve.zeroRate(expiry, daycount, ql.Continuous))
    # fore = ForDiscountCurveGen(currency_pair='USD/CNY')
    # print(fore.discount_curve.zeroRate(expiry, daycount, ql.Continuous))

