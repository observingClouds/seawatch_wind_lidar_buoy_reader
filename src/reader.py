import pandas as pd
import xarray as xr
import re
import yaml


yaml_file_path = 'config/windspeed.yaml'
with open(yaml_file_path, 'r') as file:
    input_data_fmt = yaml.safe_load(file)
vars = input_data_fmt['wsp_wdir_csv']['variable_mapping'].keys()

df = pd.read_csv(fn, skiprows=[0,1,2],  index_col=0, delimiter=';', date_format='%Y-%m-%dT%H:%M:%S%z')
df.index.name = 'time'

def read_var_structure(var, cfg=input_data_fmt):
    var_structure = input_data_fmt['wsp_wdir_csv']['variable_mapping'][var]

    return var_structure

def extract_datasubset(df, time, multi_dim_regex, multi_dim_name, var_regex, var_name):
    var_columns = df.filter(regex=var_regex)
    multi_dim = [float(re.search(multi_dim_regex, col).group(1)) for col in var_columns]
    ds = xr.Dataset({var_name: xr.DataArray(var_columns, coords={'time':time, multi_dim_name: multi_dim})})
    return ds

dss = []
for var in vars:
    dcfg = input_data_fmt['wsp_wdir_csv']['dimension_mapping']
    vcfg = read_var_structure(var)
    ds = extract_datasubset(df, df.index.to_pydatetime(),
                                vcfg["multidim"]['regex'],
                                vcfg['multidim']['name'],
                                vcfg['var_regex'], var)
    ds[var].attrs['units'] = vcfg['units']
    for dim in vcfg['dimensions']:
        ds[dim].attrs['units'] = dcfg[dim].get('units', None)
    dss.append(ds)

ds = xr.merge(dss)
    