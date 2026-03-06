#!/usr/bin/env python
# _*_ coding: utf-8 _*_
# @Time : 2026/3/6 16:41
# @Author : Kaiwei Zheng
# @Version：V 0.1
# @File : wind_cal.py
# @desc : deriving actual wind speed from wind components u and v
# Python 3.7 or above

import netCDF4 as nc
import numpy as np

def calculate_wind_speed(u_file, v_file, output_file):
    # Read u and v wind component files
    ds_u = nc.Dataset(u_file)
    ds_v = nc.Dataset(v_file)

    u_wind = ds_u.variables['10m_u_component_of_wind'][:]
    v_wind = ds_v.variables['10m_v_component_of_wind'][:]

    # Calculate wind speed
    wind_speed = np.sqrt(u_wind ** 2 + v_wind ** 2)
    ds_out = nc.Dataset(output_file, 'w', format='NETCDF4')

    # Copy dimensions from the component file
    for dim_name, dim in ds_u.dimensions.items():
        ds_out.createDimension(dim_name, len(dim) if not dim.isunlimited() else None)

    for var_name, var in ds_u.variables.items():
        if var_name not in ['10m_u_component_of_wind', '10m_v_component_of_wind']:
            out_var = ds_out.createVariable(var_name, var.datatype, var.dimensions)
            out_var.setncatts({k: var.getncattr(k) for k in var.ncattrs()})
            out_var[:] = var[:]

    # Create wind speed variable
    wind_speed_var = ds_out.createVariable('10m_wind_speed', 'f4', ('time', 'latitude', 'longitude'))
    wind_speed_var.units = 'm s**-1'
    wind_speed_var.long_name = '10m wind speed'
    wind_speed_var[:] = wind_speed

if __name__ == "__main__":
    u_file = ''
    v_file = ''
    output_dir = ''
    calculate_wind_speed(u_file, v_file, output_dir)