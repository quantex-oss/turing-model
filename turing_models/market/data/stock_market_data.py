import pandas as pd
import plotly.express as px
import os

from turing_models.market.data.plotly_layout import default_line_layout, default_xaxis_selector


def stock_market_data(stock_combined_symbol: str, start_date: str = '2020-08-01', end_date: str = '2021-08-01'):
    csv_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            f"{stock_combined_symbol}.csv",
        )

    data = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    return data.loc[start_date:end_date]


def stock_data_figure(stock_symbol: str,
                      data_types="Close",
                      start_date: str = '2020-08-01',
                      end_date: str = '2021-08-01'):
    data = stock_market_data(stock_symbol, start_date, end_date)

    fig = px.line(data, x=data.index, y=data_types, title=f"Stock Prices - {stock_symbol}")

    fig.update_xaxes(default_xaxis_selector())
    fig.update_layout(default_line_layout(x_title="Dates", y_title="Prices"))
    return fig


if __name__ == "__main__":
    df = stock_market_data("600017.SH")
    print(df)
