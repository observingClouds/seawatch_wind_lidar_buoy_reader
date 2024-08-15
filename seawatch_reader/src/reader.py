import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from . import helpers


def open_file(fn, input_file_fmt):
    df = pd.read_csv(
        fn,
        skiprows=np.arange(input_file_fmt["header"]["column_name_row"]),
        index_col=0,
        delimiter=";",
        date_format="%Y-%m-%dT%H:%M:%S%z",
    )
    df.index.name = "time"
    return df


def read_var_structure(var, cfg):
    return cfg["variable_mapping"][var]


def extract_datasubset(df, time, multi_dim_regex, multi_dim_name, var_regex, var_name):
    """Extract a single variable from the dataframe."""
    var_columns = df.filter(regex=var_regex)
    multi_dim = [float(re.search(multi_dim_regex, col).group(1)) for col in var_columns]
    return xr.Dataset(
        {
            var_name: xr.DataArray(
                var_columns, coords={"time": time, multi_dim_name: multi_dim}
            )
        }
    )


def get_location(input_file_fmt, fn):
    """Get the location from the file."""
    location = helpers.readline(fn, input_file_fmt["header"]["location"]["row"])
    loc = location.replace(input_file_fmt["header"]["location"]["identifier"], "")
    return loc.strip()


def get_position(input_file_fmt, fn):
    """Get the position of the wind lidar from the file.

    The position is determined in the following order:
    1. Directly from the configuration file
    2. From regex given in configuration file
    3. NaN if no position is found
    """
    if input_file_fmt["header"].get("position", None) is None:
        return np.nan, np.nan
    elif input_file_fmt["header"]["position"].get("lat", None) is not None:
        lat = input_file_fmt["header"]["position"]["lat"]
        lon = input_file_fmt["header"]["position"]["lon"]
        return lat, lon
    else:
        position = helpers.readline(fn, input_file_fmt["header"]["position"]["row"])
        lat = float(
            re.search(input_file_fmt["header"]["position"]["lat_regex"], position).group(
                1
            )
        )
        lon = float(
            re.search(input_file_fmt["header"]["position"]["lon_regex"], position).group(
                1
            )
        )
        return lat, lon


def get_serial(input_file_fmt, fn):
    """Get the serial number of the wind lidar from the file."""
    serial_cfg = input_file_fmt["header"].get("serial", None)
    if serial_cfg is not None:
        serial = helpers.readline(fn, input_file_fmt["header"]["system"]["row"])
        serial = serial.replace(input_file_fmt["header"]["serial"]["identifier"], "")
        return serial.strip()
    return None


def get_global_attr(input_file_fmt, fn):
    """Get the global attributes from the file."""
    pos = get_position(input_file_fmt, fn)
    return {
        "location": get_location(input_file_fmt, fn),
        "serial": get_serial(input_file_fmt, fn),
        "latitude": pos[0],
        "longitude": pos[1],
    }


def set_global_attr(ds, glb_attrs):
    """Set the global attributes to the dataset."""
    # Drop attributes with None values
    for key, value in list(glb_attrs.items()):
        if value is None:
            del glb_attrs[key]
    ds.attrs.update(glb_attrs)
    return ds


def load(fn, cfg, file_type, loc_dim=True):
    if isinstance(cfg, (str, Path)):
        cfg = helpers.read_config(cfg)
    elif isinstance(cfg, dict):
        cfg = cfg

    input_file_fmt = cfg[file_type]
    df = open_file(fn, input_file_fmt)
    glb_attrs = get_global_attr(input_file_fmt, fn)
    variables = input_file_fmt["variable_mapping"].keys()
    dss = []
    for var in variables:
        dcfg = input_file_fmt["dimension_mapping"]
        vcfg = read_var_structure(var, input_file_fmt)
        ds = extract_datasubset(
            df,
            df.index.tz_localize(None).astype("datetime64[s]").to_pydatetime(),
            vcfg["multidim"]["regex"],
            vcfg["multidim"]["name"],
            vcfg["var_regex"],
            var,
        )
        ds[var].attrs["units"] = vcfg["units"]
        for dim in vcfg["dimensions"]:
            ds[dim].attrs.update(dcfg[dim].get("attributes", {}))
            ds[dim].encoding.update(dcfg[dim].get("encoding", {}))

        if vcfg.get("additional_attributes") is not None:
            for attr in vcfg["additional_attributes"]:
                ds[var].attrs[attr] = vcfg["additional_attributes"][attr]
        dss.append(ds)

    ds = xr.merge(dss)
    if loc_dim:
        ds = ds.expand_dims("location")
        ds["location"] = [glb_attrs["location"]]
        ds["latitude"] = xr.DataArray([glb_attrs["latitude"]], dims="location")
        ds["longitude"] = xr.DataArray([glb_attrs["longitude"]], dims="location")
        del glb_attrs["latitude"]
        del glb_attrs["longitude"]
        del glb_attrs["location"]
    ds = set_global_attr(ds, glb_attrs)
    return ds


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fn", help="Path to the input file")
    parser.add_argument("--yaml_file_path", help="Path to the YAML configuration file")
    parser.add_argument(
        "--filetype", help="Type of the input file as defined in the yaml config file"
    )
    args = parser.parse_args()

    fn = args.fn
    yaml_file_path = args.yaml_file_path
    filetype = args.filetype
    ds = load(fn, yaml_file_path, filetype)
