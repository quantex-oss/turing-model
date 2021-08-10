from turing_models.utilities import TuringSchedule, TuringDate, TuringFrequencyTypes, TuringCalendarTypes, \
    TuringDateGenRuleTypes

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
