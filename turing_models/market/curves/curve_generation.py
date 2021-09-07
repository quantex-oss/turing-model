import datetime

from fundamental.turing_db.data import Turing
from turing_models.market.curves import TuringDiscountCurveZeros
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes


class CurveGeneration:
    def __init__(self,
                 annualized_term: list,
                 spot_rate: list,
                 base_date: TuringDate = TuringDate(*(datetime.date.today().timetuple()[:3])),
                 frequency_type: TuringFrequencyTypes = TuringFrequencyTypes.ANNUAL,
                 number_of_days: int = 730):
        self.term = base_date.addYears(annualized_term)
        self.spot_rate = spot_rate
        self.base_date = base_date
        self.frequency_type = frequency_type  # 传入利率的frequency type，默认是年化的
        self.number_of_days = number_of_days  # 默认是两年的自然日：365*2
        self.curve = TuringDiscountCurveZeros(self.base_date, self.term, self.spot_rate, self.frequency_type)
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
        return self.nature_days

    def get_rates(self):
        return self.nature_days_rate

    def get_data_dict(self):
        nature_days = [day.datetime() for day in self.nature_days]
        return dict(zip(nature_days, self.nature_days_rate))


class FXCurve:
    def __init__(self,
                 fx_symbol: str,
                 curve_type: str,
                 spot_rate_type: str,
                 number_of_days: int = 730):
        # TODO: 支持传枚举类型
        self.fx_symbol = fx_symbol
        self.curve_type = curve_type
        self.spot_rate_type = spot_rate_type
        self.number_of_days = number_of_days
        self.fx_asset_id = Turing.get_fx_symbol_to_id(_id=fx_symbol)['asset_id']
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
            self.set_property_list(curves_remote, "ccy1_cc_rates", "implied_interest_rate")
            self.set_property_list(curves_remote, "ccy2_cc_rates", "cny_implied_interest_rate")

    def set_property_list(self, curves_date, _property, key):
        _list = []
        for cu in curves_date:
            _list.append(cu.get(key))
        setattr(self, _property, _list)
        return _list

    def _curve_generation(self):
        self.ccy1_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy1_cc_rates,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)
        self.ccy2_curve_gen = CurveGeneration(annualized_term=self.tenors,
                                              spot_rate=self.ccy2_cc_rates,
                                              frequency_type=TuringFrequencyTypes.CONTINUOUS,
                                              number_of_days=self.number_of_days)

    def get_ccy1_data_dict(self):
        """外币利率曲线"""
        return self.ccy1_curve_gen.get_data_dict()

    def get_ccy2_data_dict(self):
        """人民币利率曲线"""
        return self.ccy2_curve_gen.get_data_dict()


if __name__ == '__main__':
    fx_curve = FXCurve(fx_symbol='USD/CNY', curve_type="Shibor3M", spot_rate_type="central")
    print(fx_curve.tenors)
    print(fx_curve.ccy1_cc_rates)
    print(fx_curve.ccy2_cc_rates)
    print(fx_curve.get_ccy1_data_dict())
    print(fx_curve.get_ccy2_data_dict())
