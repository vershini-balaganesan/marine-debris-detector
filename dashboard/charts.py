# dashboard/charts.py
"""Simple chart helpers for the dashboard — zone history line chart."""

import pandas as pd


def zone_history_dataframe(history):
    """
    Args:
        history: list of {"timestamp": ..., "count": ...} from
                 database.crud.get_zone_history(zone_id)
    Returns:
        pandas DataFrame indexed by timestamp, ready for st.line_chart.
    """
    if not history:
        return pd.DataFrame(columns=["count"])
    df = pd.DataFrame(history)
    df = df.set_index("timestamp")
    return df