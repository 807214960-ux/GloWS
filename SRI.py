#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2026/3/6 15:08
# @Author : Kaiwei Zheng
# @Version：V 0.1
# @File : SRI.py
# @desc : calculating the standardized runoff index from the streamflow series
# Python 3.7 or above

import os
import numpy as np
import pandas as pd
from scipy import stats

C0, C1, C2 = 2.515517, 0.802853, 0.010328
D1, D2, D3 = 1.432788, 0.189269, 0.001308

# Calculate SRI
def sri_from_prob(p):
    p = np.clip(p, 1e-10, 1 - 1e-10)  # Avoid errors in logarithm calculation
    k = np.where(p <= 0.5, np.sqrt(-np.log(p)), np.sqrt(-np.log(1 - p)))
    poly = (C0 + C1 * k + C2 * k * k) / (1 + D1 * k + D2 * k * k + D3 * k * k * k)
    return np.where(p <= 0.5, -(k - poly), (k - poly))

month_q_path = ''  # Path to monthly streamflow data

df = pd.read_csv(month_q_path)
df.columns = pd.to_datetime(df.columns, format="%Y-%m-%d")
df.columns = df.columns.to_period('M').to_timestamp()

eps = 1e-6  # Small value to prevent numerical errors

for n in [1, 2, 3, 4, 5, 6, 12, 24]:
    out_dir = rf"your/dir/SRI{n}"
    os.makedirs(out_dir, exist_ok=True)

    for station, row in df.iterrows():
        full = row

        # Calculate rolling accumulated values for each month
        agg = full.rolling(window=n, min_periods=n).sum()

        params = {}
        non_nan = agg.dropna()

        for month in range(1, 13):
            vals = non_nan[non_nan.index.month == month].values + eps

            # If all values are zero or no data is available, return NaN parameters
            if vals.size == 0 or np.all(vals == vals[0]):
                params[month] = (np.nan, np.nan)
            else:
                a, loc, scale = stats.gamma.fit(vals, floc=0)
                params[month] = (a, scale)

        # Calculate cumulative values and then compute SRIn
        srints = []
        for ts, x in agg.items():
            if np.isnan(x):
                srints.append(np.nan)
            else:
                a, scale = params[ts.month]
                if np.isnan(a):
                    srints.append(np.nan)
                else:
                    F = stats.gamma.cdf(x + eps, a, loc=0, scale=scale)
                    srints.append(sri_from_prob(F))

        col_name = f"SRI{n}"
        out_df = pd.DataFrame(
            data=srints,
            index=df.columns.strftime("%Y-%m"),
            columns=[col_name]
        )

        out_df.index.name = 'Time'
        out_df = out_df.dropna(subset=[col_name])

        out_path = os.path.join(out_dir, f"{station}_{col_name}.csv")
        out_df.to_csv(out_path, encoding='utf-8')