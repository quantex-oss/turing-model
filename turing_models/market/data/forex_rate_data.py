import pandas as pd
import plotly.express as px
import os

from turing_models.market.data.plotly_layout import default_line_layout, default_xaxis_selector


def forex_rate_data(forex_symbol: str, start_date: str = '2020-08-01', end_date: str = '2021-08-01'):
    csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "forex_rates.csv",
        )

    data = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    date_ranged_data = data.loc[start_date:end_date]
    return date_ranged_data[forex_symbol]


def forex_rate_figure(forex_symbol: str, start_date: str = '2020-08-01', end_date: str = '2021-08-01'):
    data = forex_rate_data(forex_symbol, start_date, end_date)

    fig = px.line(x=data.index, y=data, title=f"ForEx Rates - {forex_symbol}")

    fig.update_xaxes(default_xaxis_selector())
    fig.update_layout(default_line_layout(x_title="Dates", y_title="Rates"))
    return fig


if __name__ == "__main__":
    df = forex_rate_data("USDCNY")
    print(df)
