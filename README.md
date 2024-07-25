# SEAWATCH wind lidar buoy reader

This packages allows to read and convert CSV files provided from SEAWATCH wind lidar buoys.

This package is developed for a specific use-case and does not cover all possible scenarios. It is provided as is and without any warranty. Pull requests are welcome.

## Installation

```bash
pip install "git+ssh://github.com/observingClouds/seawatch_wind_lidar_buoy_reader#egg=seawatch_reader"
```

## Usage

The package can be used as a command line tool or as a python module.

The package assumes the following folder structure:

```
/path/to/csv/file/collection/
    |-  /Stationname_Instrument_YYYYMMDD_WindSpeedDirectionTI.csv
    |-  /Stationname_Instrument_YYYYMMDD_WindStatus.csv
    |-  /Stationname_Instrument_YYYYMMDD_CurrentData.csv
```

### Command line

```bash
seawatch_reader --path /path/to/csv/file/collection/ --output /path/to/output.nc --filetypes wsp_wdir_csv --config /path/to/config.yml
```

An example for a configuration file is provided in the `config` folder. If no configuration file is provided, the file config/windspeed.yaml is used.

### Python module
