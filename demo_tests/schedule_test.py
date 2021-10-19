from turing_models.utilities.schedule import TuringSchedule
from turing_models.utilities.turing_date import TuringDate
from turing_models.utilities.frequency import TuringFrequencyTypes
from turing_models.utilities.calendar import TuringCalendarTypes, TuringDateGenRuleTypes


effectiveDate = TuringDate(2020, 10, 1)
terminationDate = TuringDate(2021, 1, 1)
freqType: TuringFrequencyTypes = TuringFrequencyTypes.DAILY
calendarType: TuringCalendarTypes = TuringCalendarTypes.CHINA_SSE
dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
schedule = TuringSchedule(effectiveDate,
                          terminationDate,
                          freqType,
                          calendarType,
                          dateGenRuleType=dateGenRuleType)
# print(len(sorted(schedule._adjustedDates)))
print(schedule._adjustedDates)
# print(schedule._adjustedDates.index(TuringDate(2020, 4, 23)))
