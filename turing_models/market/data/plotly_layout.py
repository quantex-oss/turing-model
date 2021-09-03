def default_line_layout(x_title: str = "Dates", y_title: str = "Prices"):
    return dict(
        font_family="Arial",
        font_color="#000000",
        title_font_color="white",
        legend_title_font_color="white",
        legend_font_color="white",
        autosize=False,
        width=1280,
        height=450,
        paper_bgcolor="#1f1f1f",
        plot_bgcolor="#dddddd",

        xaxis=dict(
            title=x_title,
            titlefont=dict(
                family='Arial',
                size=12,
                color='white',
            ),
            showline=True,
            showgrid=True,
            showticklabels=True,
            linecolor='white',
            linewidth=3,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='white',
            ),
        ),
        yaxis=dict(
            title=y_title,
            titlefont=dict(
                family='Arial',
                size=12,
                color='white',
            ),
            showgrid=True,
            zeroline=False,
            showline=True,
            showticklabels=True,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='white',
            )
        )
    )


def default_xaxis_selector():
    return dict(
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )