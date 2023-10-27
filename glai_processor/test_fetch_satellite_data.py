
import pytest
import geopandas as gpd

from datetime import datetime
from pathlib import Path
from eodal.config import get_settings
from eodal.core.sensors import Sentinel2
from eodal.core.sensors import Landsat
from eodal.mapper.filter import Filter
from eodal.mapper.feature import Feature
from eodal.mapper.mapper import MapperConfigs

from fetch_satellite_data import (
    fetch_data,
    preprocess_sentinel2_scene,
    preprocess_landsat_scene)


settings = get_settings()
settings.USE_STAC = True


def test_sentinel2():

    # define the query parameters
    collection: str = 'sentinel2-msi'
    time_start: datetime = datetime(2022, 6, 1)
    time_end: datetime = datetime(2022, 6, 15)
    fpath_feature = Path('data/bbox_wtz.gpkg')
    feature = Feature.from_geoseries(
        gpd.read_file(fpath_feature).dissolve().geometry
    )
    metadata_filters: list[Filter] = [
        Filter('cloudy_pixel_percentage', '<', 50),
        Filter('processing_level', '==', 'Level-2A')
    ]
    band_selection = ['blue', 'green', 'red', 'nir_1']

    # define the scene kwargs
    scene_kwargs = {
        'scene_constructor': Sentinel2.from_safe,
        'scene_constructor_kwargs': {'band_selection': band_selection.copy(),
                                     'apply_scaling': False,
                                     'read_scl': True},
        'scene_modifier': preprocess_sentinel2_scene,
        'scene_modifier_kwargs': {'target_resolution': 10}
    }
    # define the mapper configs
    mapper_configs = MapperConfigs(
        collection=collection,
        time_start=time_start,
        time_end=time_end,
        feature=feature,
        metadata_filters=metadata_filters)

    # fetch the data
    fetch_data(
        mapper_configs=mapper_configs,
        scene_kwargs=scene_kwargs,
        band_selection=band_selection,
        output_dir=Path('data')
    )

    # make sure a GeoTiff was created
    assert Path(
        'data/S2A_2022-06-13_blue-green-red-nir_1.tiff'
    ).exists()
    # make sure the mapper configs were saved
    assert Path(
        'data/sentinel2-msi_2022-06-01-2022-06-15_mapper_configs.yaml'
    ).exists()
    # make sure the angles were saved
    assert Path(
        'data/S2A_2022-06-13_angles.yaml'
    ).exists()

    # TODO: use rio_cog to check if GeoTiff is a valid COG


def test_landsat():

    # define the query parameters
    collection: str = 'landsat-c2-l2'
    time_start: datetime = datetime(2022, 6, 1)
    time_end: datetime = datetime(2022, 6, 15)
    fpath_feature = Path('data/bbox_wtz.gpkg')
    feature = Feature.from_geoseries(
        gpd.read_file(fpath_feature).dissolve().geometry
    )
    metadata_filters: list[Filter] = [
        Filter('eo:cloud_cover', '<', 50)
    ]
    band_selection = ["blue", "green", "red", "nir08"]

    # define the scene kwargs
    scene_kwargs = {
        'scene_constructor': Landsat.from_usgs,
        'scene_constructor_kwargs': {'band_selection': band_selection.copy(),
                                     'read_qa': True},
        'scene_modifier': preprocess_landsat_scene
    }
    # define the mapper configs
    mapper_configs = MapperConfigs(
        collection=collection,
        time_start=time_start,
        time_end=time_end,
        feature=feature,
        metadata_filters=metadata_filters)

    # fetch the data
    fetch_data(
        mapper_configs=mapper_configs,
        scene_kwargs=scene_kwargs,
        band_selection=band_selection,
        output_dir=Path('data')
    )

    # make sure a GeoTiff was created
    assert Path(
        'data/LANDSAT_9_2022-06-06_blue-green-red-nir08.tiff'  # noqa E501
    ).exists()
    assert Path(
        'data/landsat-c2-l2_2022-06-01-2022-06-15_mapper_configs.yaml'
    ).exists()
    assert Path(
        'data/LANDSAT_9_2022-06-06_angles.yaml'
    ).exists()
    # TODO: use rio_cog to check if GeoTiff is a valid COG


if __name__ == '__main__':

    import os
    cwd = Path(__file__).parent.absolute()
    os.chdir(cwd.parent)

    # test_landsat()
    test_sentinel2()
