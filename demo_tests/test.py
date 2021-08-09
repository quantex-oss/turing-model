from turing_models.utilities import TuringSchedule, TuringDate, TuringFrequencyTypes, TuringCalendarTypes, \
    TuringDateGenRuleTypes

effectiveDate = TuringDate(2020, 4, 17)
terminationDate = TuringDate(2020, 5, 3)
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
print(schedule._adjustedDates.index(TuringDate(2020, 4, 23)))
