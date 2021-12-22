from typing import Union

import pandas as pd

from turing_models.utilities.helper_functions import pascal_to_snake


class EcnomicTerms:
    """"""
    def __init__(self, *args):
        self.data = {pascal_to_snake(type(arg).__name__): arg for arg in args}


class FloatingRateTerms:

    def __init__(self,
                 floating_rate_benchmark: str = None,
                 floating_spread: float = None,
                 floating_adjust_mode: str = None,
                 base_interest_rate: float = None):
        self.floating_rate_benchmark = floating_rate_benchmark
        self.floating_spread = floating_spread
        self.floating_adjust_mode = floating_adjust_mode
        self.base_interest_rate = base_interest_rate
        self.name = "浮息债"


class PrepaymentTerms:
    """
    代码示例：
    data_list = [
                {
                    "pay_date": datetime.datetime(2015, 4, 25),
                    "pay_rate": 0.04
                },
                {
                    "pay_date": datetime.datetime(2017, 4, 25),
                    "pay_rate": 0.041
                },
                {
                    "pay_date": datetime.datetime(2019, 4, 25),
                    "pay_rate": 0.042
                },
                {
                    "pay_date": datetime.datetime(2021, 4, 25),
                    "pay_rate": 0.043
                }
                ]
    data = pd.DataFrame(data=data_list)
    1、PrepaymentTerms(data=data)
    2、PrepaymentTerms(data=data_list)
    """
    def __init__(self,
                 data: Union[pd.DataFrame, list] = None):
        if data is not None and isinstance(data, list):
            self.data = pd.DataFrame(data=data)
        else:
            self.data = data
        self.name = "提前还款条款"


class EmbeddedPutableOptions:
    """
        代码示例：
        data_list = [
                    {
                        "exercise_date": datetime.datetime(2015, 4, 25),
                        "exercise_price": 100.0
                    },
                    {
                        "exercise_date": datetime.datetime(2017, 4, 25),
                        "exercise_price": 100.0
                    },
                    {
                        "exercise_date": datetime.datetime(2019, 4, 25),
                        "exercise_price": 100.0
                    },
                    {
                        "exercise_date": datetime.datetime(2021, 4, 25),
                        "exercise_price": 100.0
                    }
                    ]
        data = pd.DataFrame(data=data_list)
        1、EmbeddedPutableOptions(data=data)
        2、EmbeddedPutableOptions(data=data_list)
    """
    def __init__(self,
                 data: Union[pd.DataFrame, list] = None):
        if data is not None and isinstance(data, list):
            self.data = pd.DataFrame(data=data)
        else:
            self.data = data
        self.name = "可回售条款"


class EmbeddedRateAdjustmentOptions:
    """
        代码示例：
        data_list = [
                    {
                        "exercise_date": datetime.datetime(2015, 4, 25),
                        "high_rate_adjust": 0.07,
                        "low_rate_adjust": 0.03
                    },
                    {
                        "exercise_date": datetime.datetime(2017, 4, 25),
                        "high_rate_adjust": 0.07,
                        "low_rate_adjust": 0.03
                    },
                    {
                        "exercise_date": datetime.datetime(2019, 4, 25),
                        "high_rate_adjust": 0.07,
                        "low_rate_adjust": 0.03
                    },
                    {
                        "exercise_date": datetime.datetime(2021, 4, 25),
                        "high_rate_adjust": 0.07,
                        "low_rate_adjust": 0.03
                    }
                    ]
        data = pd.DataFrame(data=data_list)
        1、EmbeddedRateAdjustmentOptions(data=data)
        2、EmbeddedRateAdjustmentOptions(data=data_list)
    """
    def __init__(self,
                 data: Union[pd.DataFrame, list] = None):
        if data is not None and isinstance(data, list):
            self.data = pd.DataFrame(data=data)
        else:
            self.data = data
        self.name = "票面利率调整条款"


if __name__ == "__main__":
    import datetime
    floating_rate_terms = FloatingRateTerms(floating_rate_benchmark="Shibor3M",
                                            floating_spread=0.005,
                                            floating_adjust_mode="",
                                            base_interest_rate=0.02)
    data_list = [
        {
            "pay_date": datetime.datetime(2015, 4, 25),
            "pay_rate": 0.04
        },
        {
            "pay_date": datetime.datetime(2017, 4, 25),
            "pay_rate": 0.041
        },
        {
            "pay_date": datetime.datetime(2019, 4, 25),
            "pay_rate": 0.042
        },
        {
            "pay_date": datetime.datetime(2021, 4, 25),
            "pay_rate": 0.043
        }
    ]
    data = pd.DataFrame(data=data_list)
    prepayment_terms = PrepaymentTerms(data=data)
    data_list = [
        {
            "exercise_date": datetime.datetime(2015, 4, 25),
            "exercise_price": 100.0
        },
        {
            "exercise_date": datetime.datetime(2017, 4, 25),
            "exercise_price": 100.0
        },
        {
            "exercise_date": datetime.datetime(2019, 4, 25),
            "exercise_price": 100.0
        },
        {
            "exercise_date": datetime.datetime(2021, 4, 25),
            "exercise_price": 100.0
        }
    ]
    data = pd.DataFrame(data=data_list)
    embedded_putable_options = EmbeddedPutableOptions(data=data)
    data_list = [
        {
            "exercise_date": datetime.datetime(2015, 4, 25),
            "high_rate_adjust": 0.07,
            "low_rate_adjust": 0.03
        },
        {
            "exercise_date": datetime.datetime(2017, 4, 25),
            "high_rate_adjust": 0.07,
            "low_rate_adjust": 0.03
        },
        {
            "exercise_date": datetime.datetime(2019, 4, 25),
            "high_rate_adjust": 0.07,
            "low_rate_adjust": 0.03
        },
        {
            "exercise_date": datetime.datetime(2021, 4, 25),
            "high_rate_adjust": 0.07,
            "low_rate_adjust": 0.03
        }
    ]
    data = pd.DataFrame(data=data_list)
    embedded_rate_adjustment_options = EmbeddedRateAdjustmentOptions(data=data)

    ecnomic_terms = EcnomicTerms(floating_rate_terms,
                                 prepayment_terms,
                                 embedded_putable_options,
                                 embedded_rate_adjustment_options)
