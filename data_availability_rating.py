import pandas as pd
import os
from tqdm import tqdm

stations_file = ""  # Path to station information file
data_dir = ""  # Path to data directory
output_file = ""  # Path to final output file
window_sizes = [1, 3, 5, 7, 10, 15, 30, 90, 365]  # Defined window lengths

# Read station information
stations_df = pd.read_csv(stations_file)
stations = stations_df['gauge_id']
results = pd.DataFrame(columns=['gauge_id'] + [f'S{n}' for n in window_sizes])

for station in tqdm(stations, desc="Processing stations"):

    file_path = os.path.join(data_dir, station, "file_name.csv")  # Construct file path
    df = pd.read_csv(file_path)

    # Extract streamflow column
    q_series = df['streamflow']

    station_result = {'gauge_id': station}

    for n in window_sizes:
        # Count the number of windows without NaN values
        valid_windows = 0
        for i in range(len(q_series) - n + 1):
            window = q_series.iloc[i:i + n]
            if not window.isna().any():
                valid_windows += 1

        station_result[f'S{n}'] = valid_windows

    results = pd.concat([results, pd.DataFrame([station_result])], ignore_index=True)

s_columns = ['S1', 'S3', 'S7', 'S15', 'S30', 'S90', 'S365']


def score_asc(value, n):
    """
    Calculate score based on Sn
    """
    year_equivalents = [5 * 365 - (n - 1), 10 * 365 - (n - 1),
                        20 * 365 - (n - 1), 30 * 365 - (n - 1), 50 * 365 - (n - 1)]

    if value >= year_equivalents[4]:  # Greater than or equal to 50 years
        return 5
    elif value >= year_equivalents[3]:  # 30–50 years
        return 4
    elif value >= year_equivalents[2]:  # 20–30 years
        return 3
    elif value >= year_equivalents[1]:  # 10–20 years
        return 2
    elif value >= year_equivalents[0]:  # 5–10 years
        return 1
    else:  # Less than 5 years
        return 0


# Calculate scores for each Sn column
score_columns = []
for asc_col in s_columns:
    n = int(asc_col[1:])
    score_col = f"{asc_col}_score"
    score_columns.append(score_col)
    results[score_col] = results[asc_col].apply(lambda x: score_asc(x, n))

# Calculate average score
results['average_score'] = results[score_columns].mean(axis=1)


# Assign level based on average score
def assign_level(score):
    if score == 5:
        return 'I'
    elif score > 4 and score < 5:
        return 'II'
    elif score > 3 and score <= 4:
        return 'III'
    elif score > 2 and score <= 3:
        return 'IV'
    elif score > 1 and score <= 2:
        return 'V'
    elif score == 1:
        return 'VI'


results['level'] = results['average_score'].apply(assign_level)

results.to_csv(output_file, index=False)