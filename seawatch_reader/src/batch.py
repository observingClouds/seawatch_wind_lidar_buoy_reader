import argparse
import glob
import re
import sys
from pathlib import Path

import pandas as pd
import xarray as xr

from . import helpers as h
from .reader import load as rload


def apply_regex_filter(files, regex):
    filtered_files = []
    for file in files:
        match = re.search(regex, file)
        if match:
            filtered_files.append(file)

    files = filtered_files
    return files


def merge_datasets(dss):
    locations = [ds["location"] for ds in dss]
    ds_per_location = []
    for loc in locations:
        ds_per_location.append(
            xr.concat(
                [ds.sel(location=loc) for ds in dss if ds["location"] == loc],
                dim="time",
                data_vars="minimal",
            )
        )
    return xr.merge(ds_per_location)


def drop_duplicates(ds, dim="time", keep="last"):
    length = ds[dim].size
    ds_ = ds.drop_duplicates(dim, keep=keep)
    print(f"Dropped {length - ds_[dim].size} duplicates in {dim}")
    return ds_


def get_dim_independent_vars(ds, dim):
    dim_not_present = [v for v in ds.data_vars if (dim not in ds[v].dims)]
    return ds[dim_not_present]


def load(filetypes, path_to_files, cfg):
    cfg = h.read_config(cfg)
    dsss = []
    # Loop over variable sets
    for filetype in filetypes:
        if isinstance(cfg[filetype], list):
            for conf in cfg[filetype]:
                file_pattern = conf["filename_glob"]

                files = sorted(glob.glob(path_to_files + file_pattern))
                if "regex" in conf:
                    files = apply_regex_filter(files, conf["regex"])
                dss = []
                # Loop over location and time dependent files
                for file in files:
                    try:
                        ds = rload(file, {filetype: conf}, filetype)
                    except pd.errors.ParserError as e:
                        print(f"Error loading {file}: {e}")
                        continue

                    dss.append(ds)
                ds = merge_datasets(dss).sortby("time")
                ds = drop_duplicates(ds, "time", keep="last")
                dsss.append(ds)

        elif isinstance(cfg[filetype], dict):
            file_pattern = cfg[filetype]["filename_glob"]
            files = sorted(glob.glob(path_to_files + file_pattern))
            if "regex" in cfg[filetype]:
                files = apply_regex_filter(files, cfg[filetype]["regex"])

            dss = []
            # Loop over location and time dependent files
            for file in files:
                try:
                    ds = rload(file, cfg, filetype)
                except pd.errors.ParserError as e:
                    print(f"Error loading {file}: {e}")
                    continue

                dss.append(ds)
            ds = merge_datasets(dss).sortby("time")
            ds = drop_duplicates(ds, "time", keep="last")
            dsss.append(ds)
    dsss = xr.merge(dsss)
    return dsss


def main():
    parser = argparse.ArgumentParser(description="Batch processing script")
    parser.add_argument("--path", type=str, help="Path to files", required=True)
    parser.add_argument(
        "--filetypes", type=str, nargs="+", help="File types", required=True
    )
    parser.add_argument("--config", type=str, help="Path to config file", default=None)
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output file. Zarr and NetCDF file endings are excepted.",
        required=True,
    )
    args = parser.parse_args()

    if args.config is None:
        args.config = Path(__file__).parent / "../config/windspeed.yaml"

    cfg = args.config
    path_to_files = args.path
    filetypes = args.filetypes

    ds = load(filetypes, path_to_files, cfg)

    if args.output.endswith(".nc"):
        ds.to_netcdf(args.output)
    elif args.output.endswith(".zarr"):
        ds.to_zarr(args.output)
    else:
        print("Invalid output file format. Please provide either .nc or .zarr file.")


if __name__ == "__main__":
    sys.exit(main())
