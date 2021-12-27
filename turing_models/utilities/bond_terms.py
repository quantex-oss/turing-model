from datetime import datetime
from typing import List, Union

from pydantic import BaseModel


class FloatingRateTerms(BaseModel):
    floating_rate_benchmark: str = None
    floating_spread: float = None
    floating_adjust_mode: str = None
    base_interest_rate: float = None


class PrepaymentTerms(BaseModel):
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
    pay_date: Union[str, datetime] = None
    pay_rate: float = None


class EmbeddedPutableOptions(BaseModel):
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
    exercise_date: Union[str, datetime] = None
    exercise_price: float = None


class EmbeddedRateAdjustmentOptions(BaseModel):
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
    exercise_date: Union[str, datetime] = None
    high_rate_adjust: float = None
    low_rate_adjust: float = None


class EcnomicTerms(BaseModel):
    """"""
    floating_rate_terms: FloatingRateTerms
    prepayment_terms: List[PrepaymentTerms]
    embedded_putable_options: List[EmbeddedPutableOptions]
    embedded_rate_adjustment_options: List[EmbeddedRateAdjustmentOptions]

    def pay_date_list(self):
        if prepayment_terms:
            return [x.get('pay_date') for x in prepayment_terms]
        return []


if __name__ == "__main__":
    import datetime

    floating_rate_terms = {"floating_rate_benchmark": "Shibor3M",
                           "floating_spread": 0.005,
                           "floating_adjust_mode": "",
                           "base_interest_rate": 0.02}
    prepayment_terms = [
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

    embedded_putable_options = [
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
    embedded_rate_adjustment_options = [
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
    ecnomic_terms_dict = {"floating_rate_terms": floating_rate_terms, "prepayment_terms": prepayment_terms,
                          "embedded_putable_options": embedded_putable_options,
                          "embedded_rate_adjustment_options": embedded_rate_adjustment_options}

    ecnomic_terms = EcnomicTerms.parse_obj(ecnomic_terms_dict)
    print(ecnomic_terms.pay_date_list())
    print(ecnomic_terms)
