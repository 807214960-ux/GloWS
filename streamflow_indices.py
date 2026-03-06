import os
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings("ignore")

def calculate_runoff_gini(daily_flows):
    """
        Calculate Gini coefficient of streamflow series
    """
    sorted_flows = np.sort(daily_flows.dropna())
    n = len(sorted_flows)
    weights = np.arange(n, 0, -1)
    weighted_sum = np.sum(weights * sorted_flows)
    total_sum = np.sum(sorted_flows)
    if total_sum == 0:
        return np.nan
    gini = (n + 1 - 2 * (weighted_sum / total_sum)) / n
    return gini

def calculate_indices(q_dataset,output_dir, quantiles):
    """
        Calculate other streamflow indices
    """
    q_dataset["date"] = pd.to_datetime(q_dataset["date"])
    q_dataset["year"] = q_dataset["date"].dt.year
    flow_col = q_dataset.columns[1]
    q_dataset["7day_mean"] = (
        q_dataset[flow_col]
        .rolling(window=7, min_periods=7)
        .mean()
    )
    yearly_stats = q_dataset.groupby("year").apply(
        lambda group: pd.Series({
            "Mean": group[flow_col].mean(),
            "Max": group[flow_col].max(),
            "Min": group[flow_col].min(),
            "Std": group[flow_col].std(),
            "CV": (group[flow_col].std() / group[flow_col].mean()) * 100
                  if group[flow_col].mean() != 0 else np.nan,
            "Median": group[flow_col].median(),
            "Gini": calculate_runoff_gini(group[flow_col]),
            "Max_Date": (
                group.loc[group[flow_col].idxmax(), "date"].strftime("%Y-%m-%d")
                if not group[flow_col].isna().all() else np.nan
            ),
            "7day_max": group["7day_mean"].max(),
            "7day_min": group["7day_mean"].min(),
            "High_Flow_Days": (
                group[flow_col] >
                group[flow_col].quantile(0.90)
            ).sum(),
            "Low_Flow_Days": (
                group[flow_col] <
                group[flow_col].quantile(0.10)
            ).sum(),
            "Valid_Obs_Days": group[flow_col].count()
        })
    ).reset_index()
    # quantile flow
    for q in quantiles:
        yearly_stats[f"Q{int(q * 100)}"] = (
            q_dataset.groupby("year")[flow_col]
            .quantile(q)
            .values
        )

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir,
        f"runoff_indices.csv"
    )
    yearly_stats.to_csv(output_path, index=False)

def main():
    #Assume that q_path is a CSV file containing time index and a streamflow column.
    q_path = ""
    output_dir = ""
    quantiles = [0.01, 0.05, 0.10, 0.20, 0.50, 0.80, 0.90, 0.95, 0.99]
    q_dataset = pd.read_csv(q_path)
    calculate_indices(q_dataset,output_dir, quantiles)

if __name__ == "__main__":
    main()