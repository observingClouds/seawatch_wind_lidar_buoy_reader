import pandas as pd
import xarray as xr
import re
import numpy as np
import argparse
import helpers


def open_file(fn, input_file_fmt):
    df = pd.read_csv(fn, skiprows=np.arange(input_file_fmt['header']['column_name_row']),  index_col=0, delimiter=';', date_format='%Y-%m-%dT%H:%M:%S%z')
    df.index.name = 'time'
    return df

def read_var_structure(var, cfg):
    var_structure = cfg['variable_mapping'][var]

    return var_structure

def extract_datasubset(df, time, multi_dim_regex, multi_dim_name, var_regex, var_name):
    """Extract a single variable from the dataframe."""
    var_columns = df.filter(regex=var_regex)
    multi_dim = [float(re.search(multi_dim_regex, col).group(1)) for col in var_columns]
    ds = xr.Dataset({var_name: xr.DataArray(var_columns, coords={'time':time, multi_dim_name: multi_dim})})
    return ds

def get_location(input_file_fmt, fn):
    """Get the location from the file."""
    location = helpers.readline(fn, input_file_fmt['header']['location']['row'])
    loc = location.replace(input_file_fmt['header']['location']['identifier'], '')
    return loc.strip()

def get_position(input_file_fmt, fn):
    """Get the position of the wind lidar from the file."""
    position = helpers.readline(fn, input_file_fmt['header']['position']['row'])
    lat = float(re.search(input_file_fmt['header']['position']['lat_regex'], position).group(1))
    lon = float(re.search(input_file_fmt['header']['position']['lon_regex'], position).group(1))
    return lat, lon

def get_serial(input_file_fmt, fn):
    """Get the serial number of the wind lidar from the file."""
    serial_cfg = input_file_fmt['header'].get('serial', None)
    if serial_cfg is not None:
        serial = helpers.readline(fn, input_file_fmt['header']['system']['row'])
        serial = serial.replace(input_file_fmt['header']['serial']['identifier'], '')
        serial = serial.strip()
    return serial

def get_global_attr(input_file_fmt, fn):
    """Get the global attributes from the file."""
    global_attr = {}
    
    global_attr['location'] = get_location(input_file_fmt, fn)
    global_attr['latitude'], global_attr['longitude'] = get_position(input_file_fmt, fn)
    return global_attr

def set_global_attr(ds, input_file_fmt, fn):
    """Set the global attributes to the dataset."""
    global_attr = get_global_attr(input_file_fmt, fn)
    # Drop attributes with None values
    for key, value in list(global_attr.items()):
        if value is None:
            del global_attr[key]
    ds.attrs.update(global_attr)
    return ds

def load(fn, yaml_config_fn, file_type, loc_dim=True):
    input_files_fmt = helpers.read_config(yaml_config_fn)
    input_file_fmt = input_files_fmt[file_type]
    df = open_file(fn, input_file_fmt)
    vars = input_file_fmt['variable_mapping'].keys()
    dss = []
    for var in vars:
        dcfg = input_file_fmt['dimension_mapping']
        vcfg = read_var_structure(var, input_file_fmt)
        ds = extract_datasubset(df, df.index.to_pydatetime(),
                                    vcfg["multidim"]['regex'],
                                    vcfg['multidim']['name'],
                                    vcfg['var_regex'], var)
        ds[var].attrs['units'] = vcfg['units']
        for dim in vcfg['dimensions']:
            ds[dim].attrs['units'] = dcfg[dim].get('units', None)

        if vcfg.get('additional_attributes') is not None:
            for attr in vcfg['additional_attributes']:
                ds[var].attrs[attr] = vcfg['additional_attributes'][attr]
        dss.append(ds)

    ds = xr.merge(dss)
    if loc_dim:
        ds = ds.expand_dims('location')
        ds['location'] = [get_location(input_file_fmt, fn)]
    ds = set_global_attr(ds, input_file_fmt, fn)
    return ds


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fn', help='Path to the input file')
    parser.add_argument('--yaml_file_path', help='Path to the YAML configuration file')
    parser.add_argument('--filetype', help='Type of the input file as defined in the yaml config file')
    args = parser.parse_args()

    fn = args.fn
    yaml_file_path = args.yaml_file_path
    filetype = args.filetype
    ds = load(fn, yaml_file_path, filetype)