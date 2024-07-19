import glob
from reader import load
import helpers as h
import xarray as xr
import argparse

def load(filetypes, path_to_files, cfg):
    dsss = []
    for filetype in filetypes:
        files = sorted(glob.glob(path_to_files + cfg[filetype]['filename_glob']))

        dss = []
        for file in files:
            ds = load(file, args.config, filetype)
            dss.append(ds)

        ds = xr.concat(dss, dim='time')
        dsss.append(ds)
    dsss = xr.merge(dsss)
    return dsss


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Batch processing script')
    parser.add_argument('--path', type=str, help='Path to files')
    parser.add_argument('--filetypes', type=str, nargs='+', help='File types')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--output', type=str, help='Path to output file. Zarr and NetCDF file endings are excepted.')
    args = parser.parse_args()

    cfg = h.read_config(args.config)
    path_to_files = args.path
    filetypes = args.filetypes

    ds = load(filetypes, path_to_files, cfg)
    if args.output.endswith('.nc'):
        ds.to_netcdf(args.output)
    elif args.output.endswith('.zarr'):
        ds.to_zarr(args.output)
    else:
        print("Invalid output file format. Please provide either .nc or .zarr file.")