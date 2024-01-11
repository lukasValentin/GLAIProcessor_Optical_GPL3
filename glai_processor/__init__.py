"""
The glai_processor package contains the main functionality of the GLAI
processor. It is based on the eodal package and uses the rtm_inv package
for the inversion of the RTM.

Copyright (C) 2023 Lukas Valentin Graf (lukas.graf@terensis.io)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import pandas as pd
import warnings

from datetime import datetime, timedelta
from eodal.config import get_settings
from eodal.mapper.feature import Feature
from eodal.mapper.mapper import MapperConfigs
from pathlib import Path
from rtm_inv.core.lookup_table import generate_lut
from typing import Any

from glai_processor.constants import Constants, Sentinel2Constants
from glai_processor.fetch_satellite_data import fetch_data
from glai_processor.inversion import invert
from glai_processor.utils import (
    get_latest_scene,
    indicate_complete,
    load_angles,
    PLATFORMS,
    set_latest_scene
)


# setup logging and usage of STAC API for data access
settings = get_settings()
settings.USE_STAC = True
logger = settings.logger

# ignore COG creation warnings
warnings.filterwarnings("ignore")


def get_data(
    output_dir: Path,
    constants: Constants,
    feature: Feature,
    time_start: datetime,
    time_end: datetime
) -> None:
    """
    Get the satellite data for a given time period and geographic extent
    to enable GLAI retrieval.

    :param output_dir: output directory where to store the data
    :param constants: Constants object containing the scene kwargs
    :param feature: geographic feature (area) for which to get satellite data
    :time_start: start datetime for extracting satellite data
    :time_end: end datetime for extracting satellite data
    """
    # define the mapper configs
    mapper_configs = MapperConfigs(
        collection=constants.COLLECTION,
        time_start=time_start,
        time_end=time_end,
        feature=feature,
        metadata_filters=constants.METADATA_FILTERS)

    # fetch the data
    fetch_data(
        mapper_configs=mapper_configs,
        scene_kwargs=constants.SCENE_KWARGS,
        band_selection=constants.SCENE_KWARGS['scene_constructor_kwargs']['band_selection'],  # noqa E501
        output_dir=output_dir
    )


def run_rtm(
    output_dir: Path,
    constants: Constants,
    rtm_params: Path,
    traits: list[str],
    sampling_method: str = 'frs',
    lut_size: int = 50000,
    n_solutions: int = 5000,
    cost_function: str = 'rmse'
) -> None:
    """
    Run the RTM in forward mode (if required) to generate scene-specific
    lookup tables (LUTs) and peform the image inversion pixel by pixel.

    :param output_dir:
        directory with satellite data (GeoTiff files)
    :param constants:
        Constants object containing the scene kwargs
    :param rtm_params:
        RTM parametrization file
    :param traits:
        list of traits to retrieve
    :param sampling_method:
        statistical sampling method for generating the LUT
    :param lut_size:
        size of the lookup table
    :param n_solutions:
        number of solutions (matching spectral pairs with smallest cost
        function values) to aggregate into a single solution using the
        median.
    :param cost_function:
        cost function to use for the inversion.
    """
    # iterate over all angle files
    for yaml_file in output_dir.glob('S2*_angles.yaml'):

        fname_lut = yaml_file.name.replace(
            'angles.yaml', 'lut.pkl'
        )
        fpath_lut = output_dir.joinpath(fname_lut)

        # GeoTiff file containing the spectral values
        band_names_file = '-'.join(
            constants.SCENE_KWARGS[
                'scene_constructor_kwargs']['band_selection']
        ) + '.tiff'
        fname_sat_data = yaml_file.name.replace(
            'angles.yaml', band_names_file)
        fpath_sat_data = output_dir.joinpath(fname_sat_data)

        # if the LUT exists, do not overwrite
        if not fpath_lut.exists():
            # load the angles
            angles = load_angles(yaml_file)
            # get the platform from the file name
            platform = PLATFORMS[fpath_sat_data.name.split('_')[0]]

            # generate the lookup-tables using the methodology from
            # Graf et al. (2023, RSE,
            # https://doi.org/10.1016/j.rse.2023.113860)
            lut_srf = generate_lut(
                sensor=platform,
                lut_params=pd.read_csv(rtm_params),
                solar_zenith_angle=angles['solar_zenith_angle'],
                viewing_zenith_angle=angles['viewing_zenith_angle'],
                solar_azimuth_angle=angles['solar_azimuth_angle'],
                viewing_azimuth_angle=angles['viewing_azimuth_angle'],
                lut_size=lut_size,
                sampling_method=sampling_method,
                fpath_srf=constants.FPATH_SRF,
                remove_invalid_green_peaks=True,
                linearize_lai=False
            )
            lut_srf.dropna(inplace=True)
            lut_srf.to_pickle(fpath_lut)
        else:
            lut_srf = pd.read_pickle(fpath_lut)

        # invert the RTM to generate trait maps
        fpath_output = output_dir / fpath_sat_data.name.replace(
            '.tiff', '_traits.tiff')
        if not fpath_output.exists():
            invert(
                fpath_lut=fpath_lut,
                fpath_srf=fpath_sat_data,
                output_dir=output_dir,
                band_selection_lut=constants.BANDSELECTION_LUT,
                band_selection_srf=constants.SCENE_KWARGS['scene_constructor_kwargs']['band_selection'],  # noqa E501
                traits=traits,
                n_solutions=n_solutions
            )


def monitor_folder(
    folder_to_monitor: Path,
    feature: Feature,
    inversion_kwargs: dict[str, Any],
    time_start: datetime,
    time_end: datetime,
    constants: Constants = Sentinel2Constants,
    temporal_increment_days: int = 7,
) -> None:
    """
    Monitor a folder with satellite scenes and fetch new data
    automatically. This function is intended to be run as a
    cron job or similar on a regular basis. The function looks
    for the last processed scene and fetches all scenes that
    are newer than the last processed scene with a given temporal
    increment.

    The function can handle Sentinel-2 and Landsat.

    :param folder_to_monitor:
        folder to monitor with satellite scenes.
    :param feature:
        Feature object of the area of interest.
    :param inversion_kwargs:
        keyword arguments for `run_rtm`
    :param time_start:
        start of the time period to consider
    :param time_end:
        end of the time period to consider
    :param constants:
        Constants object define how to fetch the data (platform,
        scene preprocessing, etc.).
    :param temporal_increment_days:
        temporal increment in days, i.e., the function will search
        for scenes that are newer than the last processed scene
        plus this increment.
    """
    # get the latest scene to determine the start date
    last_processed_scene = get_latest_scene(
        output_dir=folder_to_monitor,
        start_time=time_start
    )
    time_start_internal = last_processed_scene + timedelta(days=1)

    # if time start is in the future, there is nothing to do
    if time_start_internal > datetime.now():
        logger.info(
            f"Start date {time_start.date()} is in the future. Exiting.")
        return
    elif time_start_internal > time_end:
        logger.info(
            f'Start date {time_start_internal.date()} is beyond end date. ' +
            'Exiting.')
        return

    # the end time for the next query will be the time stamp of the
    # last processed scene plus the temporal increment
    time_end_internal = time_start_internal + timedelta(
        days=temporal_increment_days)
    # make sure the internal end date is no later than the end data
    # given
    if time_end_internal > time_end:
        time_end_internal = time_end

    # get data
    try:
        get_data(
            output_dir=folder_to_monitor,
            constants=constants,
            time_start=time_start_internal,
            time_end=time_end_internal,
            feature=feature
        )
    except Exception as e:
        logger.error(f"Error while fetching data: {e}")

    # perform inversion (generate lookup-tables and run the inversion)
    try:
        run_rtm(
            output_dir=folder_to_monitor,
            constants=constants,
            **inversion_kwargs
        )
    except Exception as e:
        logger.error(f"Error while running RTM: {e}")

    # update the "latest scene" timestamp
    set_latest_scene(folder_to_monitor, timestamp=time_end_internal)

    # recursive function call until all the whole time period is covered
    if time_end_internal <= time_end:
        monitor_folder(
            folder_to_monitor=folder_to_monitor,
            feature=feature,
            inversion_kwargs=inversion_kwargs,
            time_start=time_start,
            time_end=time_end,
            constants=constants,
            temporal_increment_days=temporal_increment_days
        )
    else:
        indicate_complete(output_dir_scene=folder_to_monitor)
