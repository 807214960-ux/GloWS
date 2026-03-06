#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2026/3/6 13:40
# @Author : Kaiwei Zheng
# @Version：V 0.1
# @File : Multimodel_weights.py
# @desc :  generating multi-model weights based on observations and multi-model simulations
# Python 3.7 or above

import csv
import os
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform


def load_data(models, basin):
    all_data = {}
    base_path_model = r"/path/to/models/data"
    base_path_obs = r"/path/to/observation/data"

    # Load observation data
    path_obs = os.path.join(base_path_obs, f'{basin}.csv')
    obs_df = pd.read_csv(path_obs, header=0, parse_dates=['time'], names=['time', 'obs'])
    obs_df = obs_df.set_index('time')
    all_data['obs'] = obs_df['obs']

    # Load model data
    for model in models:
        path_model = os.path.join(base_path_model, model, f'{basin}.csv')
        model_df = pd.read_csv(path_model, header=0, parse_dates=['time'], names=['time', model])
        model_df = model_df.set_index('time')
        all_data[model] = model_df[model]

    result_df = pd.DataFrame(all_data)
    result_df = result_df.sort_index()
    return result_df


def dis_matrix(result_df):
    """Calculate the distance matrix between models"""
    model_names = result_df.columns.tolist()
    data = result_df.T.values
    distances = pdist(data, metric='euclidean')
    distance_matrix = squareform(distances)
    return pd.DataFrame(distance_matrix, index=model_names, columns=model_names)


def obs_weight(ojld):
    """Calculate model weights"""

    # Determine similarity threshold using the distance between observation and models
    obs_col = ojld.loc[ojld.index != 'obs', 'obs']
    obs_mu = np.mean(obs_col)
    obs_normalized = obs_col / obs_mu
    obs_normalized_min = np.min(obs_normalized)
    D_u = 0.48 * obs_normalized_min

    # Extract model submatrix and calculate independence weights
    gcm_columns = [col for col in ojld.columns if col != 'obs']
    gcm_dist = ojld.loc[gcm_columns, gcm_columns]
    mask = ~np.eye(len(gcm_columns), dtype=bool)
    gcm_mu = np.mean(gcm_dist.values[mask])
    S = np.exp(-(gcm_dist.values / (gcm_mu * D_u)) ** 2)
    np.fill_diagonal(S, 1.0)
    R_u = 1 + np.sum(S, axis=1) - np.diag(S)
    weights_u = {model: 1 / R for model, R in zip(gcm_columns, R_u)}

    # Calculate performance weights based on observation distance
    D_q = 0.7 * obs_normalized_min
    weights_q = {model: np.exp(-(norm_dist / D_q) ** 2)
                 for model, norm_dist in zip(gcm_columns, obs_normalized.values)}

    # Combine independence weight and performance weight
    combined_weights = {model: (weights_u[model] * weights_q[model])
                        for model in gcm_columns}

    # Normalize weights
    total = sum(combined_weights.values())
    combined_weights = {model: w / total for model, w in combined_weights.items()}

    return combined_weights


def main():

    # Example models
    models = ['model1', 'model2', 'model3', 'model4', 'model5']
    basin = 'basin_01'

    result_df = load_data(models, basin)
    distance = dis_matrix(result_df)
    weights = obs_weight(distance)

    output_file = "model_weights.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['basin'] + list(weights.keys()))
        writer.writerow([basin] + [f"{w:.6f}" for w in weights.values()])
    print(f"Saved {output_file}")


if __name__ == "__main__":
    main()