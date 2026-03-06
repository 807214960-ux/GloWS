# GloWS
This repository stores custom code used to generate the Global Large-Sample Watershed Synthesis dataset (GloWS). The dataset covers 23,029 basins from 24 international, national, and sub-national sources. GloWS is generated after rigorous station screening, careful visual inspection using Google Map satellite imagery, and systematic data quality control. This dataset includes metadata, hydrological indices, 14 meteorological variables, land-use and land-cover characteristics, water storage terms, and other static attributes. To empower future projections and assess climate change impacts, GloWS also includes nine daily catchment-mean bias-corrected variables from 22 Global Climate Models (GCMs) under the Coupled Model Intercomparison Project Phase 6 (CMIP6), and provides the multi-model ensemble mean scenarios throughout the 21st century. 

The following are brief descriptions of each script.
data_availability_rating.py:The script for generating data availability scores and ratings.
grid_data_weights.py:The script for generating grid area weights based on grids and polygons.
Multimodel_weights.py:The script for generating multi-model weights based on observations and multi-model simulations.
RHSH_cal.py:The script for deriving relative humidity and specific humidity from other meteorological variables.
SRI.py:The script for calculating the standardized runoff index from the streamflow series.
streamflow_indices.py:The script for calculating statistical indicators of streamflow from the streamflow series.
wind_cal.py:The script for deriving actual wind speed from wind components u and v.

For any inquiry about the dataset, welcome to contact Kaiwei Zheng (kaiweiz@whu.edu.cn)
