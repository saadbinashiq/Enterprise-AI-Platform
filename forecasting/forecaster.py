"""
Forecasting engine.

Uses statsmodels' Holt-Winters exponential smoothing rather than Prophet --
same job (trend + seasonality forecasting), far lighter to install (no
cmdstan/pystan compiler toolchain required), which matters in classroom or
restricted environments. The case study's "Technical Requirements" lists
Prophet explicitly; if you have it available, swap the model call below for
`Prophet().fit(df).predict(future)`. The input/output shape here (ds/y in,
yhat/yhat_lower/yhat_upper out) is deliberately Prophet-compatible so that
swap is a few lines, not a rewrite.
"""
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from db.database import engine


def forecast_revenue(store_id: int = None, periods: int = 30, seasonal_period: int = 7) -> pd.DataFrame:
    """
    Forecasts total daily revenue (optionally filtered to one store).
    Returns a DataFrame with columns: ds, yhat, yhat_lower, yhat_upper
    """
    query = "SELECT date, revenue FROM sales"
    if store_id is not None:
        query += f" WHERE store_id = {int(store_id)}"
    sales_df = pd.read_sql(query, engine)

    df = sales_df.groupby("date")["revenue"].sum().reset_index()
    df.columns = ["ds", "y"]
    df["ds"] = pd.to_datetime(df["ds"])
    df = df.set_index("ds").asfreq("D").ffill().reset_index()

    model = ExponentialSmoothing(
        df["y"], trend="add", seasonal="add", seasonal_periods=seasonal_period,
        initialization_method="estimated",
    ).fit()

    forecast_values = model.forecast(periods)
    resid_std = model.resid.std()

    last_date = df["ds"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=periods, freq="D")

    return pd.DataFrame({
        "ds": future_dates,
        "yhat": forecast_values.values,
        "yhat_lower": forecast_values.values - 1.96 * resid_std,
        "yhat_upper": forecast_values.values + 1.96 * resid_std,
    })


if __name__ == "__main__":
    fc = forecast_revenue(periods=14)
    print(fc.round(2).to_string(index=False))
