'''
Run the PROSAIL RTM forward model to generate a lookup-table
for the given sensor and angles.
'''

import pandas as pd

from pathlib import Path
from rtm_inv.core.lookup_table import generate_lut


# DEFINE THE URLS TO THE REQUIRED DATA
BASE_URL = \
    'https://raw.githubusercontent.com/EOA-team/sentinel2_crop_trait_timeseries/main'  # noqa E501
FPATH_SRF = \
    f'{BASE_URL}/data/auxiliary/S2-SRF_COPE-GSEG-EOPG-TN-15-0007_3.1.xlsx'
RTM_PARAMS = \
    f'{BASE_URL}/src/lut_params/prosail_danner-etal_stemelongation-endofheading.csv'  # noqa E501

LUT_SIZE = 100
SAMPLING_METHOD = 'frs'

PLATFORMS = {'S2A': 'Sentinel2A', 'S2B': 'Sentinel2B'}


def get_required_angles(
        angles: dict[str, float]
) -> dict[str, float]:
    """
    Make sure all required angles are present in the
    angles dictionary. If not, use the default values.

    :param angles:
        dictionary containing the angles
    :return:
        dictionary containing the angles
    """
    required_angles = {}
    required_angles['solar_zenith_angle'] = \
        angles.get('sun_zenith_angle', 45)
    required_angles['solar_azimuth_angle'] = \
        angles.get('sun_azimuth_angle', 180)
    required_angles['viewing_zenith_angle'] = \
        angles.get('sensor_zenith_angle', 0)
    required_angles['viewing_azimuth_angle'] = \
        angles.get('sensor_azimuth_angle', 180)
    return required_angles


def load_angles(
        fpath_angles: Path
) -> dict[str, float]:
    """
    Load the viewing and illumination angles from a YAML file.

    :param fpath_angles:
        path to the YAML file containing the angles
    :return:
        dictionary containing the angles
    """
    import yaml
    with open(fpath_angles, 'r') as src:
        angles = yaml.safe_load(src)

    # make sure all required angles are present
    return get_required_angles(angles)


if __name__ == '__main__':

    import os
    cwd = Path(__file__).parent.absolute()
    os.chdir(cwd.parent)

    # TODO: make more generic and include landsat

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
