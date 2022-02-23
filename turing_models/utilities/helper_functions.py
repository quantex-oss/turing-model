import datetime
import re
import sys
from typing import Union

import numpy as np
from numba import njit, float64
import QuantLib as ql

from turing_utils.log.request_id_log import logger
from turing_models.utilities.day_count import DayCountType, TuringDayCount
from turing_models.utilities.error import TuringError
from turing_models.utilities.global_variables import gDaysInYear, gSmall
from turing_models.utilities.turing_date import TuringDate
from turing_models.models.model_black_scholes_analytical import bs_value, bs_delta


###############################################################################


def _funcName():
    ''' Extract calling function name - using a protected method is not that
    advisable but calling inspect.stack is so slow it must be avoided. '''
    ff = sys._getframe().f_back.f_code.co_name
    return ff


###############################################################################

def gridIndex(t, gridTimes):
    n = len(gridTimes)
    for i in range(0, n):
        gridTime = gridTimes[i]
        if abs(gridTime - t) < gSmall:
            print(t, gridTimes, i)
            return i

    raise TuringError("Grid index not found")


###############################################################################


def betaVectorToCorrMatrix(betas):
    ''' Convert a one-factor vector of factor weights to a square correlation
    matrix. '''

    numAssets = len(betas)
    correlation = np.ones(shape=(numAssets, numAssets))
    for i in range(0, numAssets):
        for j in range(0, i):
            c = betas[i] * betas[j]
            correlation[i, j] = c
            correlation[j, i] = c

    return np.array(correlation)


###############################################################################


def pv01Times(t: float,
              f: float):
    ''' Calculate a bond style pv01 by calculating remaining coupon times for a
    bond with t years to maturity and a coupon frequency of f. The order of the
    list is reverse time order - it starts with the last coupon date and ends
    with the first coupon date. '''

    dt = 1.0 / f
    pv01Times = []

    while t >= 0.0:
        pv01Times.append(t)
        t -= dt

    return pv01Times


###############################################################################


def timesFromDates(dt: TuringDate,
                   valuationDate: TuringDate,
                   dayCountType: DayCountType = None):
    ''' If a single date is passed in then return the year from valuation date
    but if a whole vector of dates is passed in then convert to a vector of
    times from the valuation date. The output is always a numpy vector of times
    which has only one element if the input is only one date. '''

    if isinstance(valuationDate, TuringDate) is False:
        raise TuringError("Valuation date is not a TuringDate")

    if dayCountType is None:
        dcCounter = None
    else:
        dcCounter = TuringDayCount(dayCountType)

    if isinstance(dt, TuringDate):
        numDates = 1
        times = [None]
        if dcCounter is None:
            times[0] = (dt - valuationDate) / gDaysInYear
        else:
            times[0] = dcCounter.yearFrac(valuationDate, dt)[0]

        return times[0]

    elif isinstance(dt, list) and isinstance(dt[0], TuringDate):
        numDates = len(dt)
        times = []
        for i in range(0, numDates):
            if dcCounter is None:
                t = (dt[i] - valuationDate) / gDaysInYear
            else:
                t = dcCounter.yearFrac(valuationDate, dt[i])[0]
            times.append(t)

        return np.array(times)

    elif isinstance(dt, np.ndarray):
        raise TuringError("You passed an ndarray instead of dates.")
    else:
        raise TuringError("Discount factor must take dates.")


###############################################################################


def checkVectorDifferences(x: np.ndarray,
                           y: np.ndarray,
                           tol: float = 1e-6):
    ''' Compare two vectors elementwise to see if they are more different than
    tolerance. '''

    n1 = len(x)
    n2 = len(y)
    if n1 != n2:
        raise TuringError("Vectors x and y do not have same size.")

    for i in range(0, n1):
        diff = x[i] - y[i]
        if abs(diff) > tol:
            print("Vector difference of:", diff, " at index: ", i)


###############################################################################


def checkDate(d: TuringDate):
    ''' Check that input d is a TuringDate. '''

    if isinstance(d, TuringDate) is False:
        raise TuringError("Should be a date dummy!")


###############################################################################


def dump(obj):
    ''' Get a list of all of the attributes of a class (not built in ones) '''

    attrs = dir(obj)

    non_function_attributes = [attr for attr in attrs
                               if not callable(getattr(obj, attr))]

    non_internal_attributes = [attr for attr in non_function_attributes
                               if not attr.startswith('__')]

    private_attributes = [attr for attr in non_internal_attributes
                          if attr.startswith('_')]

    public_attributes = [attr for attr in non_internal_attributes
                         if not attr.startswith('_')]

    print("PRIVATE ATTRIBUTES")
    for attr in private_attributes:
        x = getattr(obj, attr)
        print(attr, x)

    print("PUBLIC ATTRIBUTES")
    for attr in public_attributes:
        x = getattr(obj, attr)
        print(attr, x)


###############################################################################


def printTree(array: np.ndarray,
              depth: int = None):
    ''' Function that prints a binomial or trinonial tree to screen for the
    purpose of debugging. '''
    n1, n2 = array.shape

    if depth is not None:
        n1 = depth

    for j in range(0, n2):
        for i in range(0, n1):
            x = array[i, n2 - j - 1]
            if x != 0.0:
                print("%10.5f" % x, end="")
            else:
                print("%10s" % '-', end="")
        print("")


###############################################################################


def inputTime(dt: TuringDate,
              curve):
    ''' Validates a time input in relation to a curve. If it is a float then
    it returns a float as long as it is positive. If it is a TuringDate then it
    converts it to a float. If it is a Numpy array then it returns the array
    as long as it is all positive. '''

    small = 1e-8

    def check(t):
        if t < 0.0:
            raise TuringError("Date " + str(dt) +
                              " is before curve date " + str(curve._curveDate))
        elif t < small:
            t = small
        return t

    if isinstance(dt, float):
        t = dt
        return check(t)
    elif isinstance(dt, TuringDate):
        t = (dt - curve._valuationDate) / gDaysInYear
        return check(t)
    elif isinstance(dt, np.ndarray):
        t = dt
        if np.any(t) < 0:
            raise TuringError("Date is before curve value date.")
        t = np.maximum(small, t)
        return t
    else:
        raise TuringError("Unknown type.")


###############################################################################


@njit(fastmath=True, cache=True)
def listdiff(a: np.ndarray,
             b: np.ndarray):
    ''' Calculate a vector of differences between two equal sized vectors. '''

    if len(a) != len(b):
        raise TuringError("Cannot diff lists with different sizes")

    diff = []
    for x, y in zip(a, b):
        diff.append(x - y)

    return diff


###############################################################################


@njit(fastmath=True, cache=True)
def dotproduct(xVector: np.ndarray,
               yVector: np.ndarray):
    ''' Fast calculation of dot product using Numba. '''

    dotprod = 0.0
    n = len(xVector)
    for i in range(0, n):
        dotprod += xVector[i] * yVector[i]
    return dotprod


###############################################################################


@njit(fastmath=True, cache=True)
def frange(start: int,
           stop: int,
           step: int):
    ''' fast range function that takes start value, stop value and step. '''
    x = []
    while start <= stop:
        x.append(start)
        start += step

    return x


###############################################################################


@njit(fastmath=True, cache=True)
def normaliseWeights(wtVector: np.ndarray):
    ''' Normalise a vector of weights so that they sum up to 1.0. '''

    n = len(wtVector)
    sumWts = 0.0
    for i in range(0, n):
        sumWts += wtVector[i]
    for i in range(0, n):
        wtVector[i] = wtVector[i] / sumWts
    return wtVector


###############################################################################


def to_string(label: str,
              value: (float, str),
              separator: str = "\n",
              listFormat: bool = False):
    ''' Format label/value pairs for a unified formatting. '''
    # Format option for lists such that all values are aligned:
    # Label: value1
    #        value2
    #        ...
    label = str(label)

    if listFormat and type(value) is list and len(value) > 0:
        s = label + ": "
        labelSpacing = " " * len(s)
        s += str(value[0])

        for v in value[1:]:
            s += "\n" + labelSpacing + str(v)
        s += separator

        return s
    else:
        return f"{label}: {value}{separator}"


###############################################################################


def tableToString(header: str,
                  valueTable,
                  floatPrecision="10.7f"):
    ''' Format a 2D array into a table-like string. '''
    if (len(valueTable) == 0 or type(valueTable) is not list):
        print(len(valueTable))
        return ""

    numRows = len(valueTable[0])

    s = header + "\n"
    for i in range(numRows):
        for vList in valueTable:
            # isinstance is needed instead of type in case of pandas floats
            if (isinstance(vList[i], float)):
                s += format(vList[i], floatPrecision) + ", "
            else:
                s += str(vList[i]) + ", "
        s = s[:-2] + "\n"

    return s[:-1]


###############################################################################


def toUsableType(t):
    ''' Convert a type such that it can be used with `isinstance` '''
    if hasattr(t, '__origin__'):
        origin = t.__origin__
        # t comes from the `typing` module
        if origin is list:
            return (list, np.ndarray)
        elif origin is Union:
            types = t.__args__
            return tuple(toUsableType(tp) for tp in types)
    else:
        # t is a normal type
        if t is float:
            return (int, float, np.float64)
        if isinstance(t, tuple):
            return tuple(toUsableType(tp) for tp in t)

    return t


###############################################################################


@njit(float64(float64, float64[:], float64[:]), fastmath=True, cache=True)
def uniformToDefaultTime(u, t, v):
    ''' Fast mapping of a uniform random variable to a default time given a
    survival probability curve. '''

    if u == 0.0:
        return 99999.0

    if u == 1.0:
        return 0.0

    numPoints = len(v)
    index = 0

    for i in range(1, numPoints):
        if u <= v[i - 1] and u > v[i]:
            index = i
            break

    if index == numPoints + 1:
        t1 = t[numPoints - 1]
        q1 = v[numPoints - 1]
        t2 = t[numPoints]
        q2 = v[numPoints]
        lam = np.log(q1 / q2) / (t2 - t1)
        tau = t2 - np.log(u / q2) / lam
    else:
        t1 = t[index - 1]
        q1 = v[index - 1]
        t2 = t[index]
        q2 = v[index]
        tau = (t1 * np.log(q2 / u) + t2 * np.log(u / q1)) / np.log(q2 / q1)

    return tau


###############################################################################
# THIS IS NOT USED

@njit(fastmath=True, cache=True)
def accruedTree(gridTimes: np.ndarray,
                gridFlows: np.ndarray,
                face: float):
    ''' Fast calulation of accrued interest using an Actual/Actual type of
    convention. This does not calculate according to other conventions. '''

    numGridTimes = len(gridTimes)

    if len(gridFlows) != numGridTimes:
        raise TuringError("Grid flows not same size as grid times.")

    accrued = np.zeros(numGridTimes)

    # When the grid time is before the first coupon we have to extrapolate back

    couponTimes = np.zeros(0)
    couponFlows = np.zeros(0)

    for iGrid in range(1, numGridTimes):

        cpnTime = gridTimes[iGrid]
        cpnFlow = gridFlows[iGrid]

        if gridFlows[iGrid] > gSmall:
            couponTimes = np.append(couponTimes, cpnTime)
            couponFlows = np.append(couponFlows, cpnFlow)

    numCoupons = len(couponTimes)

    # interpolate between coupons
    for iGrid in range(0, numGridTimes):
        t = gridTimes[iGrid]
        for i in range(0, numCoupons):
            if t > couponTimes[i - 1] and t <= couponTimes[i]:
                den = couponTimes[i] - couponTimes[i - 1]
                num = (t - couponTimes[i - 1])
                accrued[iGrid] = face * num * couponFlows[i] / den
                break

    return accrued


###############################################################################


def checkArgumentTypes(func, values):
    ''' Check that all values passed into a function are of the same type
    as the function annotations. If a value has not been annotated, it
    will not be checked. '''
    for valueName, annotationType in func.__annotations__.items():
        value = values[valueName]
        if value is None:
            continue
        usableType = toUsableType(annotationType)
        if (not isinstance(value, usableType)):
            print("ERROR with function arguments for", func.__name__)
            print("This is in module", func.__module__)
            print("Please check inputs for argument >>", valueName, "<<")
            print("You have input an argument", value, "of type", type(value))
            print("The allowed types are", usableType)
            print("It is none of these so FAILS. Please amend.")
            #            s = f"In {func.__module__}.{func.__name__}:\n"
            #            s += f"Mismatched Types: expected a "
            #            s += f"{valueName} of type '{usableType.__name__}', however"
            #            s += f" a value of type '{type(value).__name__}' was given."
            raise TuringError("Argument Type Error")


###############################################################################


def convert_argument_type(self, func, values):
    """将时间的str格式转换为TuringDate"""
    for value_name, annotation_type in func.__annotations__.items():
        if value_name != 'return':
            value = values[value_name]
            if value is None:
                continue
            if annotation_type is TuringDate and type(value) is str:
                """注释类型是TuringDate，但实际传入是str，
                则将str类型转成对应的TuringDate类型"""
                if value.isdigit():
                    """只支持传入'%Y%m%d'格式的字符串时间"""
                    __value = TuringDate.fromString(value)
                elif '-' in str(value):
                    __value = TuringDate.fromString(value, '%Y-%m-%d')
                setattr(self, value_name, __value)


def pascal_to_snake(camel_case: str):
    """驼峰转下划线"""
    snake_case = re.sub(r"(?P<key>[A-Z])", r"_\g<key>", camel_case)
    return snake_case.lower().strip('_')


def turingdate_to_qldate(date: TuringDate):
    """ Convert TuringDate to ql.Date """
    if date is not None:
        if isinstance(date, TuringDate):
            return ql.Date(date._d, date._m, date._y)
        elif isinstance(date, list) and all(isinstance(dt, TuringDate) for dt in date):
            return [ql.Date(dt._d, dt._m, dt._y) for dt in date]
        elif isinstance(date, ql.Date):
            return date
        elif isinstance(date, list) and all(isinstance(dt, ql.Date) for dt in date):
            return date
        else:
            raise TuringError('Please check the input of date')


def datetime_to_turingdate(date):
    """ Convert datetime to TuringDate """
    if date is not None:
        if isinstance(date, (datetime.datetime, datetime.date)):
            return TuringDate(date.year, date.month, date.day)
        elif isinstance(date, list) and all(isinstance(dt, (datetime.datetime, datetime.date)) for dt in date):
            return [TuringDate(dt.year, dt.month, dt.day) for dt in date]
        elif isinstance(date, TuringDate):
            return date
        elif isinstance(date, list) and all(isinstance(dt, TuringDate) for dt in date):
            return date
        else:
            raise TuringError('Please check the input of date')


def datetime_to_qldate(date):
    """ Convert datetime to ql.Date """
    if date is not None:
        if isinstance(date, (datetime.datetime, datetime.date)):
            return ql.Date(date.day, date.month, date.year)
        elif isinstance(date, list) and all(isinstance(dt, (datetime.datetime, datetime.date)) for dt in date):
            return [ql.Date(dt.day, dt.month, dt.year) for dt in date]
        elif isinstance(date, ql.Date):
            return date
        elif isinstance(date, list) and all(isinstance(dt, ql.Date) for dt in date):
            return date
        else:
            raise TuringError('Please check the input of date')


def date_str_to_datetime(date_str):
    """例：2021-08-04T00:00:00.000+0800（字符串）转datetime"""
    date_str = ' '.join(date_str.split('+')[0].split('T'))[:-4]
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def convert_date(column_name: str):
    """提供给pd.DataFrame的apply方法使用，把str转成datetime.datetime"""
    def fun(x):
        if isinstance(x[column_name], str):
            return date_str_to_datetime(x[column_name])
        else:
            return x[column_name]
    return fun


def utc2local(utc_dtm):
    # UTC 时间转本地时间（ +8:00 ）
    local_tm = datetime.datetime.fromtimestamp(0)
    utc_tm = datetime.datetime.utcfromtimestamp(0)
    offset = local_tm - utc_tm
    return utc_dtm + offset


def to_datetime(date: Union[str, datetime.datetime, datetime.date, TuringDate]) -> datetime.datetime:
    if date is None:
        return None
    if isinstance(date, datetime.datetime):
        return date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif isinstance(date, datetime.date):
        return datetime.datetime(date.year, date.month, date.day)
    elif isinstance(date, TuringDate):
        return datetime.datetime(date._y, date._m, date._d)
    try:
        if date == 'latest':
            return datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        fmt = "%Y%m%d"
        if '-' not in str(date):
            date = datetime.datetime.strptime(str(date), fmt)
        if '-' in str(date):
            if len(str(date)) == 10:
                fmt = "%Y-%m-%d"
            elif len(str(date)) == 19:
                fmt = "%Y-%m-%d %H:%M:%S"
            else:
                fmt = "%Y-%m-%dT%H:%M:%S.%f%z"
            date = datetime.datetime.strptime(str(date), fmt)
        date = utc2local(date)
        res_tuple = (date.year, date.month, date.day,)
        return datetime.datetime(*res_tuple)
    except ValueError as e:
        logger.debug(str(e))
    except Exception as e:
        logger.debug(str(e))


def to_turing_date(res: Union[str,
                              datetime.datetime,
                              datetime.date,
                              TuringDate,
                              list]) -> Union[TuringDate, list]:
    if res is None:
        return None
    if isinstance(res, TuringDate):
        return res
    elif isinstance(res, (datetime.datetime, datetime.date)):
        res_tuple = (res.year, res.month, res.day)
        return TuringDate(*res_tuple)
    elif isinstance(res, list):
        return [to_turing_date(dt) for dt in res]
    try:
        if res == 'latest':
            return TuringDate(*(datetime.date.today().timetuple()[:3]))
        fmt = "%Y%m%d"
        if '-' not in str(res):
            res = datetime.datetime.strptime(str(res), fmt)
        if '-' in str(res):
            if len(str(res)) == 10:
                fmt = "%Y-%m-%d"
            elif len(str(res)) == 19:
                fmt = "%Y-%m-%d %H:%M:%S"
            else:
                fmt = "%Y-%m-%d %H:%M:%S"
                res = ' '.join(res.split('+')[0].split('T'))[:-4]
            res = datetime.datetime.strptime(str(res), fmt)
        res = utc2local(res)
        res_tuple = (res.year, res.month, res.day,)
        return TuringDate(*res_tuple)
    except ValueError as e:
        logger.debug(str(e))
    except Exception as e:
        logger.debug(str(e))


bump = 1e-4


def calculate_greek(obj, price, attr, bump=1e-4, order=1, cus_inc=None):
    """
    obj: 实例对象
    price: 用于做差分计算的方法
    attr: 需要修改的属性名，str格式
    如果要传cus_inc，格式须为(函数名, 函数参数值)
    """
    cus_func = args = None
    attr_value = getattr(obj, attr)  # 先保留属性的原始值
    if cus_inc:
        cus_func, args = cus_inc

    def increment(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(args * count)
        else:
            _attr_value += count * bump
        setattr(obj, attr, _attr_value)

    def decrement(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(-args * count)
        else:
            _attr_value -= count * bump
        setattr(obj, attr, _attr_value)

    def recover():
        setattr(obj, attr, attr_value)

    if order == 1:
        if isinstance(attr_value, TuringDate):
            p0 = price()
            increment(attr_value)
            p_up = price()
            recover()
            return (p_up - p0) / bump
        increment(attr_value)
        p_up = price()
        decrement(attr_value)
        p_down = price()
        recover()
        return (p_up - p_down) / (bump * 2)
    elif order == 2:
        p0 = price()
        decrement(attr_value)
        p_down = price()
        increment(attr_value)
        p_up = price()
        recover()
        return (p_up - 2.0 * p0 + p_down) / bump / bump


def greek(obj, price, attr, bump=bump, order=1, cus_inc=None):
    """
    如果要传cus_inc，格式须为(函数名, 函数参数值)
    """
    cus_func = args = None
    attr_value = getattr(obj, attr)
    if cus_inc:
        cus_func, args = cus_inc

    def increment(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(args * count)
        else:
            _attr_value += count * bump
        setattr(obj, attr, _attr_value)

    def decrement(_attr_value, count=1):
        if cus_func:
            _attr_value = cus_func(-args * count)
        else:
            _attr_value -= count * bump
        setattr(obj, attr, _attr_value)

    def clear():
        setattr(obj, attr, None)

    if order == 1:
        if isinstance(attr_value, TuringDate):
            p0 = price()
            increment(attr_value)
            p_up = price()
            clear()
            return (p_up - p0) / bump
        increment(attr_value)
        p_up = price()
        clear()
        decrement(attr_value)
        p_down = price()
        clear()
        return (p_up - p_down) / (bump * 2)
    elif order == 2:
        p0 = price()
        decrement(attr_value)
        p_down = price()
        increment(attr_value)
        p_up = price()
        clear()
        return (p_up - 2.0 * p0 + p_down) / bump / bump


@njit(fastmath=True, cache=True)
def fastDelta(s, t, k, rd, rf, vol, deltaTypeValue, optionTypeValue):
    ''' Calculation of the FX Option delta. Used in the determination of
    the volatility surface. Avoids discount curve interpolation so it
    should be slightly faster than the full calculation of delta. '''

    pips_spot_delta = bs_delta(s, t, k, rd, rf, vol, optionTypeValue, False)
    from turing_models.instruments.common import TuringFXDeltaMethod

    if deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA.value:
        return pips_spot_delta
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA.value:
        pips_fwd_delta = pips_spot_delta * np.exp(rf * t)
        return pips_fwd_delta
    elif deltaTypeValue == TuringFXDeltaMethod.SPOT_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_spot_delta_prem_adj = pips_spot_delta - vpctf
        return pct_spot_delta_prem_adj
    elif deltaTypeValue == TuringFXDeltaMethod.FORWARD_DELTA_PREM_ADJ.value:
        vpctf = bs_value(s, t, k, rd, rf, vol, optionTypeValue, False) / s
        pct_fwd_delta_prem_adj = np.exp(rf * t) * (pips_spot_delta - vpctf)
        return pct_fwd_delta_prem_adj
    else:
        raise TuringError("Unknown TuringFXDeltaMethod")


def newton_fun(y, *args):
    """ Function is used by scipy.optimize.newton """
    self = args[0]  # 实例对象
    price = args[1]  # 对照的标准
    attr = args[2]  # 需要调整的参数
    fun = args[3]  # 调整参数后需重新计算的方法
    setattr(self, attr, y)  # 调整参数
    px = getattr(self, fun)()  # 重新计算方法的返回值
    obj_fn = px - price  # 计算误差
    return obj_fn
