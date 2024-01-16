"""
Low-level tests of the glai_processor package (unit test).
This test suite is run using pytest.
"""

import pytest  # noqa F401
import geopandas as gpd
import pandas as pd

from datetime import datetime
from pathlib import Path
from eodal.config import get_settings
from eodal.core.raster import RasterCollection
from eodal.core.sensors import Sentinel2
from eodal.core.sensors import Landsat
from eodal.mapper.filter import Filter
from eodal.mapper.feature import Feature
from eodal.mapper.mapper import MapperConfigs
from rtm_inv.core.lookup_table import generate_lut

from glai_processor.fetch_satellite_data import fetch_data
from glai_processor.constants import (
    preprocess_sentinel2_scene,
    preprocess_landsat_scene)
from glai_processor.inversion import invert
from glai_processor.utils import (
    load_angles,
    PLATFORMS
)

settings = get_settings()
settings.USE_STAC = True

FPATH_SRF = 'https://github.com/EOA-team/sentinel2_crop_traits/raw/main/data/auxiliary/S2-SRF_COPE-GSEG-EOPG-TN-15-0007_3.1.xlsx'  # noqa
RTM_PARAMS = 'https://raw.githubusercontent.com/EOA-team/sentinel2_crop_trait_timeseries/main/src/lut_params/prosail_danner-etal_all_phases.csv'  # noqa
SAMPLING_METHOD = 'frs'


def test_sentinel2():
    """
    Test the fetch_data function for Sentinel-2.
    """

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
    """
    Test the fetch_data function for Landsat.
    """
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


def test_run_rtm_forward():
    """
    Run the PROSAIL RTM forward model to generate a lookup-table
    for the given sensor and angles.
    """
    # define the angle yaml file
    fpath_angles = Path('data/S2A_2022-06-13_angles.yaml')
    # load the angles
    angles = load_angles(fpath_angles)
    assert len(angles) == 4

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
        lut_size=100,  # to speed up testing
        sampling_method=SAMPLING_METHOD,
        fpath_srf=FPATH_SRF,
        remove_invalid_green_peaks=True,
        linearize_lai=False
    )
    assert not lut_srf.empty
    # save the lookup-tables
    lut_srf.dropna(inplace=True)
    assert not lut_srf.empty
    fpath_lut = Path('data/S2A_2022-06-13_lut.pkl')
    lut_srf.to_pickle(fpath_lut)
    assert fpath_lut.exists()


def test_inversion():
    """
    Test the inversion of the RTM.
    """
    # define the lookup-table
    fpath_lut = Path('data/S2A_2022-06-13_lut.pkl')
    # define the GeoTiff file containing the spectral values
    fpath_srf = Path('data/S2A_2022-06-13_blue-green-red-nir_1.tiff')
    # define the output directory
    output_dir = Path('data')
    # define the band selection for the lookup-table
    band_selection_lut = ['B02', 'B03', 'B04', 'B08']
    # define the band selection for the spectral values
    band_selection_srf = ['blue', 'red', 'green', 'nir_1']
    # define the traits to be retrieved
    traits = ['lai', 'cab']

    # invert the RTM
    invert(
        fpath_lut=fpath_lut,
        fpath_srf=fpath_srf,
        output_dir=output_dir,
        band_selection_lut=band_selection_lut,
        band_selection_srf=band_selection_srf,
        traits=traits
    )

    # make sure the traits were saved
    trait_path = Path(
        'data/S2A_2022-06-13_blue-green-red-nir_1_traits.tiff'
    )
    assert trait_path.exists()

    # read the data and make sure the traits are in the file
    traits = RasterCollection.from_multi_band_raster(trait_path)
    assert 'lai' in traits.band_names
    assert 'cab' in traits.band_names
