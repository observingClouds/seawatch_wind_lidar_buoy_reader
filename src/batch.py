import argparse
import glob

import xarray as xr

import helpers as h
from reader import load as rload


def get_dim_independent_vars(ds, dim):
    dim_not_present = [v for v in ds.data_vars if (dim not in ds[v].dims)]
    return ds[dim_not_present]


def load(filetypes, path_to_files, cfg_file):
    cfg = h.read_config(cfg_file)
    dsss = []
    # Loop over variable sets
    for filetype in filetypes:
        file_pattern = cfg[filetype]["filename_glob"]
        files = sorted(glob.glob(path_to_files + file_pattern))

        dss = []
        # Loop over location and time dependent files
        for file in files:
            ds = rload(file, cfg_file, filetype)
            dss.append(ds)

        # time_indep_vars = get_dim_independent_vars(dss[0], 'time')
        ds = xr.concat(dss, dim="time", data_vars="minimal", compat="no_conflicts")
        # ds_fields = xr.concat(dss, dim='location', data_vars=time_indep_vars.data_vars)
        # ds = xr.merge([ds, ds_fields])
        dsss.append(ds)
    dsss = xr.merge(dsss)
    return dsss


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch processing script")
    parser.add_argument("--path", type=str, help="Path to files")
    parser.add_argument("--filetypes", type=str, nargs="+", help="File types")
    parser.add_argument("--config", type=str, help="Path to config file")
    parser.add_argument(
        "--output",
        type=str,
        help="Path to output file. Zarr and NetCDF file endings are excepted.",
    )
    args = parser.parse_args()

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
