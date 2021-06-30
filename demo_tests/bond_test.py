import numpy as np

from fundamental.market.curves.discount_curve_zeros import TuringDiscountCurveZeros

from turing_models.utilities.turing_date import TuringDate
from fundamental.pricing_context import PricingContext
from turing_models.instrument.bond import Bond
from turing_models.instrument.bond_fixed_rate import Bond as Bond1


dates = [0.083, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7, 7.5, 8, 8.5, 9, 9.5, 10]
rates = [1.8124, 1.8848, 2.0986, 2.3175, 2.4012, 2.5515, 2.7018, 2.7638, 2.8259, 2.867, 2.9081, 2.9499, 2.9917, 3.0246,
         3.0575, 3.091, 3.1244, 3.1235, 3.1226, 3.122, 3.1213, 3.1209, 3.1204]
# zero_rates = np.array(rates)
bond = Bond1(quantity=2,
             bond_type='BOND',
             coupon=0.03,
             issue_date=TuringDate(2021, 1, 1),
             due_date=TuringDate(2026, 1, 1),
             freq_type='每年付息',
             accrual_type='30/360',
             par=100,
             clean_price=98,
             ytm=0.051,
             zero_dates=dates,
             zero_rates=rates)

# settlement_date = TuringDate(2021, 6, 28)
# expiry = TuringDate(2021, 9, 28)
# zero_dates = settlement_date.addYears(dates)
# curve = TuringDiscountCurveZeros(valuationDate=settlement_date, zeroDates=zero_dates, zeroRates=rates)
# print(curve.zeroRate(expiry))
# print('full_price_from_ytm:', bond.full_price_from_ytm())
# print('principal:', bond.principal())

print('dv01:', bond.dv01())
print('dollar_duration:', bond.dollar_duration())
print('macauley_duration:', bond.macauley_duration())
print('modified_duration:', bond.modified_duration())
print('dollar_convexity:', bond.dollar_convexity())
print('principal:', bond.principal())
print('full_price_from_ytm:', bond.full_price_from_ytm())
print('clean_price_from_ytm:', bond.clean_price_from_ytm())
print('full_price_from_discount_curve:', bond.full_price_from_discount_curve())
print('clean_price_from_discount_curve:', bond.clean_price_from_discount_curve())
print('current_yield:', bond.current_yield())
print('yield_to_maturity:', bond.yield_to_maturity())
print('calc_accrued_interest:', bond.calc_accrued_interest())
