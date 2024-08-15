import xarray as xr

from seawatch_reader.src.reader import load


def test_load_cfg1(
    cfg="./config/config_onevar.yaml",
    test_file="./data/MOCK-1_M01_WindSpeedDirectionTI.csv",
):
    # Load the test file using the reader module
    ds = load(test_file, cfg, "wsp_wdir_csv")

    # Assert that the returned object is an xarray Dataset
    assert isinstance(ds, xr.Dataset)

    # Assert that the dataset contains the expected variables
    expected_variables = ["w"]
    assert all(var in ds.variables for var in expected_variables)

    # Assert that the dataset has the expected dimensions
    expected_dimensions = ["time", "location", "height"]
    assert all(dim in ds.dims for dim in expected_dimensions)

    # Assert that the dataset location is correct
    assert ds.location == "MOCK-UP STATION 1 (MOCK-1)"

    # Assert that the position is correct
    assert ds.latitude == 50.12345 and ds.longitude == -10.12345

    # Assert that the dataset variables have the expected attributes
    expected_var_attrs = {
        "w": {
            "units": "m/s",
            "standard_name": "upward_air_velocity",
            "description": "Vertical wind speed",
        },
    }
    for var in expected_var_attrs:
        assert all(
            ds[var].attrs[attr] == expected_var_attrs[var][attr]
            for attr in expected_var_attrs[var]
        )


def test_load_pos_in_cfg(
    cfg="./config/config_givenposition.yaml",
    test_file="./data/MOCK-1_M01_WindSpeedDirectionTI.csv",
):
    # Load the test file using the reader module
    ds = load(test_file, cfg, "wsp_wdir_csv")

    # Assert that the position is correct
    assert ds.latitude == 20.0 and ds.longitude == 50.0
