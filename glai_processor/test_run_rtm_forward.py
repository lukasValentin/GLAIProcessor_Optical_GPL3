
import pandas as pd

from pathlib import Path
from rtm_inv.core.lookup_table import generate_lut

from glai_processor.utils import (
    load_angles,
    FPATH_SRF,
    LUT_SIZE,
    PLATFORMS,
    SAMPLING_METHOD,
    RTM_PARAMS)


def test_run_rtm_forward():
    """
    Run the PROSAIL RTM forward model to generate a lookup-table
    for the given sensor and angles.
    """
    # define the angle yaml file
    fpath_angles = Path('data/S2A_2022-06-13_angles.yaml')
    # load the angles
    angles = load_angles(fpath_angles)

    # GeoTiff file containing the spectral values
    fpath_srf = Path('data/S2A_2022-06-13_B02-B03-B04-B08-SCL.tiff')
    # get the platform from the file name
    platform = PLATFORMS[fpath_srf.name.split('_')[0]]

    # generate the lookup-tables using the methodology from
    # Graf et al. (2023, RSE, https://doi.org/10.1016/j.rse.2023.113860)
    lut_srf = generate_lut(
        sensor=platform,
        lut_params=pd.read_csv(RTM_PARAMS),
        solar_zenith_angle=angles['solar_zenith_angle'],
        viewing_zenith_angle=angles['viewing_zenith_angle'],
        solar_azimuth_angle=angles['solar_azimuth_angle'],
        viewing_azimuth_angle=angles['viewing_azimuth_angle'],
        lut_size=LUT_SIZE,
        sampling_method=SAMPLING_METHOD,
        fpath_srf=FPATH_SRF,
        remove_invalid_green_peaks=True,
        linearize_lai=False
    )

    # save the lookup-tables
    lut_srf.dropna(inplace=True)
    fpath_lut = Path('data/S2A_2022-06-13_lut.pkl')
    lut_srf.to_pickle(fpath_lut)
