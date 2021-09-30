import datetime

import pandas as pd

from fundamental.turing_db.data import Turing, TuringDB
from turing_models.instruments.common import CurrencyPair, RMBIRCurveType, SpotExchangeRateType
from turing_models.instruments.rates.irs import create_ibor_single_curve
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
                 value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))):
        self.value_date = value_date
        shibor_curve = getattr(self, 'shibor_curve_data', None) or TuringDB.shibor_curve(date=value_date)
        print("shibor_curve_data:", shibor_curve)
        shibor_deposit_tenors = shibor_curve['tenor'][:5]
        shibor_deposit_rates = shibor_curve['rate'][:5]
        shibor_3m_curve = getattr(self, 'irs_curve_data', None) or \
                          TuringDB.irs_curve(curve_type='Shibor3M', date=value_date)['Shibor3M']
        print("irs_curve_data:", shibor_3m_curve)
        swap_curve_tenors = shibor_3m_curve['tenor']
        swap_curve_rates = shibor_3m_curve['average']

        self.tenors = shibor_deposit_tenors + swap_curve_tenors
        # 转成TuringDate格式
        self.dates = value_date.addYears(self.tenors)
        self.dom_curve = create_ibor_single_curve(value_date,
                                                  shibor_deposit_tenors,
                                                  shibor_deposit_rates,
                                                  TuringDayCountTypes.ACT_365F,
                                                  swap_curve_tenors,
                                                  TuringSwapTypes.PAY,
                                                  swap_curve_rates,
                                                  TuringFrequencyTypes.QUARTERLY,
                                                  TuringDayCountTypes.ACT_365F, 0)

    @property
    def discount_curve(self):
        return self.dom_curve


class ForDiscountCurveGen:
    """生成外币折现曲线"""

    def __init__(self,
                 currency_pair: str,
                 value_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3]))):
        self.value_date = value_date
        fx_asset_id = Turing.get_fx_asset_id_by_symbol(symbol=currency_pair)
        future_data = getattr(self, 'swap_curve_data', None) or \
                      TuringDB.swap_curve(asset_id=fx_asset_id, date=value_date)[fx_asset_id]
        future_tenors = future_data['tenor']
        future_quotes = future_data['swap_point']
        print("swap_curve_data:", future_data)
        self.future_dates = value_date.addYears(future_tenors)
        exchange_rate = getattr(self, 'exchange_rate_data', None) or \
                        TuringDB.exchange_rate(symbol=currency_pair, date=value_date)[currency_pair]
        print("exchange_rate_data:", exchange_rate)
        self.fwd_dfs = []
        for quote in future_quotes:
            self.fwd_dfs.append(exchange_rate / (exchange_rate + quote))
        dom_discount_curve_gen = DomDiscountCurveGen(value_date)
        self.domestic_discount_curve = dom_discount_curve_gen.discount_curve
        _tenors = dom_discount_curve_gen.tenors
        self.dates = value_date.addYears(_tenors)
        self.fx_forward_curve = TuringDiscountCurve(value_date, self.future_dates, self.fwd_dfs)

    @property
    def discount_curve(self):
        return TuringDiscountCurveFXImplied(self.value_date,
                                            self.dates,
                                            self.domestic_discount_curve,
                                            self.fx_forward_curve)


if __name__ == '__main__':
    fx_curve = FXIRCurve(fx_symbol=CurrencyPair.USDCNY,
                         curve_type=RMBIRCurveType.Shibor3M,
                         spot_rate_type=SpotExchangeRateType.Central)
    print('CCY1 Curve\n', fx_curve.get_ccy1_curve())
    print('CCY2 Curve\n', fx_curve.get_ccy2_curve())
