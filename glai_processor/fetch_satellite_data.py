"""
Interface to fetch optical satellite data to run the GLAI
processor.

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

import os
import planetary_computer
import tempfile
import uuid
import urllib.request
import yaml

from pathlib import Path
from eodal.mapper.mapper import Mapper, MapperConfigs
from eodal.metadata.sentinel2.parsing import parse_MTD_TL


def angles_from_mspc(url: str) -> dict[str, float]:
    """
    Extract viewing and illumination angles from MS Planetary Computer
    metadata XML (this is a work-around until STAC provides the angles
    directly)

    :param url:
        URL to the metadata XML file
    :returns:
        extracted angles as dictionary
    """
    response = urllib.request.urlopen(planetary_computer.sign_url(url)).read()
    temp_file = os.path.join(tempfile.gettempdir(), f'{uuid.uuid4()}.xml')
    with open(temp_file, 'wb') as dst:
        dst.write(response)

    metadata = parse_MTD_TL(in_file=temp_file)
    # get sensor zenith and azimuth angle
    sensor_angles = ['SENSOR_ZENITH_ANGLE', 'SENSOR_AZIMUTH_ANGLE']
    sensor_angle_dict = {
        k: v for k, v in metadata.items() if k in sensor_angles}
    return sensor_angle_dict


def fetch_data(
        mapper_configs: MapperConfigs,
        output_dir: Path,
        scene_kwargs: dict = None,
        band_selection: list[str] = ['red', 'green', 'blue', 'nir_1']
) -> None:
    """
    Fetch satellite data from STAC API. Each scene is stored
    as a cloud-optimized GeoTIFF alongside the scene angles
    as yaml file.

    Parameters
    ----------
    mapper_configs : MapperConfigs
        MapperConfigs object.
    output_dir : Path
        Output directory to save data to.
    scene_kwargs: dict
        kwargs for reading the scene into EOdal
    :band_selection:
        name of the spectral bands to fetch
    """
    # query the scenes available (no I/O of scenes, this only fetches metadata)
    mapper = Mapper(mapper_configs)
    mapper.query_scenes()

    # if no data is found return
    if mapper.metadata.empty:
        return

    # load the angular information. Unfortunately, this is not yet
    # available in the STAC metadata, so we need to fetch it from
    # the original metadata.
    if mapper_configs.collection == 'sentinel2-msi':
        mapper.metadata['href_xml'] = mapper.metadata.assets.apply(
            lambda x: x['granule-metadata']['href']
        )
        mapper.metadata['sensor_angles'] = mapper.metadata['href_xml'].apply(
            lambda x, angles_from_mspc=angles_from_mspc: angles_from_mspc(x)
        )
        mapper.metadata['sensor_zenith_angle'] = \
            mapper.metadata['sensor_angles'].apply(
                lambda x: x['SENSOR_ZENITH_ANGLE'])
        mapper.metadata['sensor_azimuth_angle'] = \
            mapper.metadata['sensor_angles'].apply(
                lambda x: x['SENSOR_AZIMUTH_ANGLE'])
    # TODO: add Landsat angles

    # load the scenes available from STAC
    mapper.load_scenes(scene_kwargs=scene_kwargs)

    # save scenes as cloud-optimized GeoTiff
    band_str = '-'.join(band_selection)
    for timestamp, scene in mapper.data:
        platform = scene.scene_properties.platform
        scene.to_rasterio(
            output_dir / f'{platform}_{timestamp.date()}_{band_str}.tiff',
            band_selection=band_selection,
            as_cog=True)
        # save the relevant metadata as yaml
        fpath_metadata = output_dir.joinpath(
            f'{platform}_{timestamp.date()}_angles.yaml')
        # select metadata by timestamp rounded to seconds
        metadata = mapper.metadata[
            mapper.metadata.sensing_time.dt.round('S').dt.strftime(
                '%Y-%m-%d %H:%M:%S') ==
            timestamp.strftime('%Y-%m-%d %H:%M:%S')].copy()
        # select only the angles
        angle_columns = [
            x for x in metadata.columns if 'angle' in x
            and x != 'sensor_angles']
        # save the metadata as yaml
        angle_dict = metadata[angle_columns].to_dict('records')[0]
        with open(fpath_metadata, 'w') as dst:
            yaml.dump(angle_dict, dst)

    # to enhance reproducibility and provide proper documentation, the
    # MapperConfigs are saved as yaml (and can be loaded again from yaml)
    fpath_mapper_configs = output_dir.joinpath(
        f'{mapper_configs.collection}_{mapper_configs.time_start.date()}-' +
        f'{mapper_configs.time_end.date()}_mapper_configs.yaml'
    )
    mapper_configs.to_yaml(fpath_mapper_configs)
