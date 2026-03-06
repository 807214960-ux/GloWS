#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2026/3/6 13:18
# @Author : Kaiwei Zheng
# @Version：V 0.1
# @File : grid_data_weights.py
# @desc : generating grid area weights based on grids and polygons
# Python 3.7 or above


import json
import time
import numpy as np
import netCDF4 as nc
import geopandas as gpd
from shapely.geometry import box
from shapely.validation import make_valid
from multiprocessing import Pool, cpu_count, Manager


def calculate_overlap(cell_geom, basin_geom):
    """Calculate the intersection between a grid cell and the basin boundary"""
    if not basin_geom.is_valid:
        basin_geom = make_valid(basin_geom)  # Fix invalid geometry
    inter = cell_geom.intersection(basin_geom)
    return inter.area / basin_geom.area if not inter.is_empty else 0.0


def weight_calculate(lon, lat, boundary, resolution):
    """Expect lon and lat as global 1D longitude/latitude arrays.
    boundary is a single basin boundary. Note that longitude ranges
    may differ among different gridded datasets."""

    # Create buffer distance
    buffer = resolution / 2

    # Handle buffered basin boundary
    min_lon, min_lat, max_lon, max_lat = boundary.total_bounds
    bounds = {k: v + (buffer if 'max' in k else -buffer)
              for k, v in zip(['min_lon', 'min_lat', 'max_lon', 'max_lat'],
                              [min_lon, min_lat, max_lon, max_lat])}

    # Extract buffered boundary values
    buffered_min_lon = bounds['min_lon']
    buffered_min_lat = bounds['min_lat']
    buffered_max_lon = bounds['max_lon']
    buffered_max_lat = bounds['max_lat']

    # Filter longitude and latitude and determine projection CRS
    filtered_lon = lon[(lon >= buffered_min_lon) & (lon <= buffered_max_lon)]
    filtered_lat = lat[(lat >= buffered_min_lat) & (lat <= buffered_max_lat)]

    mean_lon = np.mean(filtered_lon)
    mean_lat = np.mean(filtered_lat)

    utm_zone = int((mean_lon + 180) / 6) + 1
    is_northern = mean_lat >= 0
    utm_crs = f"EPSG:326{utm_zone:02d}" if is_northern else f"EPSG:327{utm_zone:02d}"

    # Generate grid polygons
    half_res = resolution / 2
    grid_polygons = []

    for lon in filtered_lon:
        for lat in filtered_lat:
            cell = box(lon - half_res, lat - half_res, lon + half_res, lat + half_res)
            grid_polygons.append({'latitude': lat, 'longitude': lon, 'geometry': cell})

    grid_gdf = gpd.GeoDataFrame(grid_polygons, crs="EPSG:4326")

    # Project to UTM coordinate system and calculate intersections
    grid_gdf_proj = grid_gdf.to_crs(utm_crs)
    boundary_proj = boundary.to_crs(utm_crs)
    basin_union_proj = boundary_proj.geometry.union_all()

    grid_gdf_proj["weight"] = grid_gdf_proj["geometry"].apply(
        lambda geom: calculate_overlap(geom, basin_union_proj))

    # Remove unnecessary data
    grid_gdf_proj = grid_gdf_proj.drop(columns=["geometry"])
    grid_gdf_proj = grid_gdf_proj[grid_gdf_proj["weight"] > 0]

    grid_gdf_proj['longitude'] = grid_gdf_proj['longitude'].apply(
        lambda x: x + 360 if x < 0 else x)

    return grid_gdf_proj


def process_basin(basin, lon, lat, global_weights, resolution):
    """Process a single basin"""
    gauge_id = basin['gauge_id'].iloc[0]
    weights = weight_calculate(lon, lat, basin, resolution)
    global_weights[gauge_id] = weights
    return gauge_id


if __name__ == "__main__":
    start_time = time.time()

    sample_nc_path = ''
    shp_file = ''
    resolution = 0.1  # Adjust according to the resolution of your gridded dataset

    gdf = gpd.read_file(shp_file)
    data_grids = nc.Dataset(sample_nc_path)

    lon = data_grids["longitude"][:]
    lat = data_grids["latitude"][:]

    with Manager() as manager:
        global_weights = manager.dict()

        basins = [gdf[gdf['gauge_id'] == gauge_id]
                  for gauge_id in gdf['gauge_id'][:1].unique()]

        for basin in basins:
            process_basin(basin, lon, lat, global_weights, resolution)

        global_weights = dict(global_weights)

    json_data = {}

    for gauge_id, weights in global_weights.items():
        # Create a dictionary for each basin where grid points are keys and weights are values
        point_weight_dict = dict(
            zip([f"{lon},{lat}" for lon, lat in weights[['longitude', 'latitude']].to_numpy()],
                weights['weight'].to_numpy())
        )

        json_data[gauge_id] = point_weight_dict

    with open(r"global_weights.json", 'w') as f:
        json.dump(json_data, f)