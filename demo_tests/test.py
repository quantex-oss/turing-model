from turing_models.utilities import TuringSchedule, TuringDate, TuringFrequencyTypes, TuringCalendarTypes, \
    TuringDateGenRuleTypes

effectiveDate = TuringDate(2020, 4, 17)
terminationDate = TuringDate(2020, 11, 3)
freqType: TuringFrequencyTypes = TuringFrequencyTypes.MONTHLY
calendarType: TuringCalendarTypes = TuringCalendarTypes.CHINA_SSE
dateGenRuleType = TuringDateGenRuleTypes.BACKWARD
schedule = TuringSchedule(effectiveDate,
                          terminationDate,
                          freqType,
                          calendarType,
                          dateGenRuleType=dateGenRuleType)
print(len(schedule._adjustedDates))
