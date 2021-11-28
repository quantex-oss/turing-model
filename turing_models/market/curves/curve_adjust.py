import datetime

from turing_models.market.curves.discount_curve_zeros import TuringDiscountCurveZeros
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.error import TuringError
from turing_models.utilities.turing_date import TuringDate


class CurveAdjust:

    def __init__(self,
                 dates: list,
                 rates: list,
                 parallel_shift=None,
                 curve_shift=None,
                 pivot_point=None,
                 tenor_start=None,
                 tenor_end=None):
        self.dates = dates
        self.rates = rates
        if parallel_shift:
            self.parallel_shift = parallel_shift * 0.0001
        if curve_shift:
            self.curve_shift = curve_shift * 0.0001
        self.pivot_point = pivot_point  # 单位：年
        self.tenor_start = tenor_start  # 单位：年
        self.tenor_end = tenor_end  # 单位：年

        self.today = TuringDate(*(datetime.date.today().timetuple()[:3]))
        self.pivot_rate = None
        self.start_rate = None
        self.end_rate = None
        self.pivot_index = None
        self.start_index = None
        self.end_index = None
        self.curve_parallel_shift()

        if curve_shift:
            if not self.pivot_point:
                self.pivot_point = self.dates[0]

            if self.pivot_point > self.dates[-1] or self.pivot_point < self.dates[0]:
                raise TuringError("Please check the input of pivot_point")

            self.confirm_center_point()
            self.modify_data()
            self.get_data_index()
            self.rotate_curve()

    def curve_parallel_shift(self):
        if hasattr(self, "parallel_shift"):
            self.rates = [x + self.parallel_shift for x in self.rates]

    def confirm_center_point(self):
        dates = self.today.addYears(self.dates)
        curve = TuringDiscountCurveZeros(self.today, dates, self.rates)
        point_date = self.today.addYears(self.pivot_point)
        self.pivot_rate = curve.zeroRate(
            point_date, freqType=TuringFrequencyTypes.ANNUAL)

        if self.tenor_start:
            start_date = self.today.addYears(self.tenor_start)
            self.start_rate = curve.zeroRate(
                start_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_start = self.dates[0]
            self.start_rate = self.rates[0]

        if self.tenor_end:
            end_date = self.today.addYears(self.tenor_end)
            self.end_rate = curve.zeroRate(
                end_date, freqType=TuringFrequencyTypes.ANNUAL)
        else:
            self.tenor_end = self.dates[-1]
            self.end_rate = self.rates[-1]

    def modify_data(self):
        if self.pivot_point not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.pivot_point:
                    break
            self.dates.insert(i, self.pivot_point)
            self.rates.insert(i, self.pivot_rate)

        if self.tenor_start not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_start:
                    break
            self.dates.insert(i, self.tenor_start)
            self.rates.insert(i, self.start_rate)

        if self.tenor_end not in self.dates:
            dates_copy = self.dates.copy()
            for i in range(len(dates_copy)):
                if dates_copy[i] > self.tenor_end:
                    self.dates.insert(i, self.tenor_end)
                    self.rates.insert(i, self.end_rate)
                    return
            self.dates.append(self.tenor_end)
            self.rates.append(self.end_rate)


    def get_data_index(self):
        self.pivot_index = self.dates.index(self.pivot_point)
        self.start_index = self.dates.index(self.tenor_start)
        self.end_index = self.dates.index(self.tenor_end)

    def rotate_curve(self):
        rates_copy = self.rates.copy()
        dr = self.curve_shift / (self.end_index - self.start_index)
        for i in range(len(rates_copy)):
            if i >= self.start_index and i <= self.end_index:
                self.rates[i] = (i - self.pivot_index) * dr + rates_copy[i]
            elif i < self.start_index:
                self.rates[i] = (self.start_index -
                                 self.pivot_index) * dr + rates_copy[i]
            elif i > self.end_index:
                self.rates[i] = (self.end_index -
                                 self.pivot_index) * dr + rates_copy[i]

    def get_dates_result(self):
        return self.dates

    def get_rates_result(self):
        return self.rates

    def get_data_dict(self):
        return dict(zip(self.dates, self.rates))
