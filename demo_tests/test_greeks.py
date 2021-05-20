import sys
sys.path.append("..")

from turing_models.products.equity import TuringOptionTypes, \
     TuringEquityVanillaOption, TuringEquityAmericanOption, \
     TuringEquityAsianOption, TuringAsianOptionValuationMethods
from turing_models.models.model_black_scholes import TuringModelBlackScholes
from turing_models.market.curves import TuringDiscountCurveFlat
from turing_models.utilities.turing_date import TuringDate

value_date = TuringDate(y=2021, m=4, d=25)
expiry_date = TuringDate(y=2021, m=7, d=25)
start_averaging_date = TuringDate(y=2021, m=6, d=25)
strike_price = 500
volatility = 0.02

stock_price = 510
interest_rate = 0.03
dividend_yield = 0

# Model Definition
bs_model = TuringModelBlackScholes(volatility)
discount_curve = TuringDiscountCurveFlat(
    value_date,
    interest_rate)
dividend_curve = TuringDiscountCurveFlat(
    value_date,
    dividend_yield)

european_option = TuringEquityVanillaOption(
        expiry_date, strike_price, TuringOptionTypes.EUROPEAN_CALL)

american_option = TuringEquityAmericanOption(
        expiry_date, strike_price, TuringOptionTypes.AMERICAN_CALL)

asian_option = TuringEquityAsianOption(
    start_averaging_date, expiry_date,
    stock_price, TuringOptionTypes.ASIAN_CALL)

european_option_delta = european_option.delta(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)
european_option_gamma = european_option.gamma(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)
european_option_vega = european_option.vega(value_date,
                                            stock_price,
                                            discount_curve,
                                            dividend_curve,
                                            bs_model)
european_option_theta = european_option.theta(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)

european_option_rho = european_option.rho(value_date,
                                          stock_price,
                                          discount_curve,
                                          dividend_curve,
                                          bs_model)

american_option_delta = american_option.delta(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)
american_option_gamma = american_option.gamma(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)
american_option_vega = american_option.vega(value_date,
                                            stock_price,
                                            discount_curve,
                                            dividend_curve,
                                            bs_model)
american_option_theta = american_option.theta(value_date,
                                              stock_price,
                                              discount_curve,
                                              dividend_curve,
                                              bs_model)
american_option_rho = american_option.rho(value_date,
                                          stock_price,
                                          discount_curve,
                                          dividend_curve,
                                          bs_model)
asian_option_delta = asian_option.delta(value_date,
                                        stock_price,
                                        discount_curve,
                                        dividend_curve,
                                        bs_model,
                                        TuringAsianOptionValuationMethods.GEOMETRIC)
asian_option_gamma = asian_option.gamma(value_date,
                                        stock_price,
                                        discount_curve,
                                        dividend_curve,
                                        bs_model,
                                        TuringAsianOptionValuationMethods.GEOMETRIC)
asian_option_vega = asian_option.vega(value_date,
                                      stock_price,
                                      discount_curve,
                                      dividend_curve,
                                      bs_model,
                                      TuringAsianOptionValuationMethods.GEOMETRIC)
asian_option_theta = asian_option.theta(value_date,
                                        stock_price,
                                        discount_curve,
                                        dividend_curve,
                                        bs_model,
                                        TuringAsianOptionValuationMethods.GEOMETRIC)
asian_option_rho = asian_option.rho(value_date,
                                    stock_price,
                                    discount_curve,
                                    dividend_curve,
                                    bs_model,
                                    TuringAsianOptionValuationMethods.GEOMETRIC)
print(f'European Option: {european_option_delta} {european_option_gamma} {european_option_vega} {european_option_theta} {european_option_rho}')
print(f'American Option: {american_option_delta} {american_option_gamma} {american_option_vega} {american_option_theta} {american_option_rho}')
print(f'Asian Option: {asian_option_delta} {asian_option_gamma} {asian_option_vega} {asian_option_theta} {asian_option_rho}')
