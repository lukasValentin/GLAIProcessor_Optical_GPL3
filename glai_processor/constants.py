"""
Constants for the GLAIProcessor package defining how to handle
Sentinel-2 and Landsat scenes.

Copyright (C) 2024 Terensis

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

from __future__ import annotations

from eodal.core.sensors import Landsat, Sentinel2
from eodal.mapper.filter import Filter


def preprocess_landsat_scene(
        ds: Landsat
) -> Landsat:
    """
    Mask clouds and cloud shadows in a Landsat scene based
    on the 'qa_pixel' band.

    :param ds:
        Landsat scene before cloud mask applied.
    :return:
        Landsat scene with clouds and cloud shadows masked.
    """
    ds.mask_clouds_and_shadows(inplace=True)
    return ds


def preprocess_sentinel2_scene(
    ds: Sentinel2
) -> Sentinel2:
    """
    Resample a Sentinel-2 scene and mask clouds, shadows, and snow
    based on the Scene Classification Layer (SCL).

    :returns:
        resampled, cloud-masked Sentinel-2 scene.
    """
    # resample scene
    ds.resample(inplace=True, target_resolution=10)
    # mask clouds, shadows, and snow
    ds.mask_clouds_and_shadows(inplace=True)
    return ds


class Constants:
    """
    Constants for the eodal_viewer package.
    """
    pass


class LandsatC2L1Constants(Constants):
    """Constants for Landsat Collection 2 Level 1 scenes."""
    # name of the collection to query (Sentinel-2)
    COLLECTION: str = 'landsat-c2-l1'

    # filters to apply to the metadata
    # - only scenes with less than 80% cloudy pixels
    # - only scenes with processing level 'Level-2A'
    METADATA_FILTERS: list[Filter] = [
        Filter('eo:cloud_cover', '<', 80)
    ]

    # kwargs for the scene constructor
    # - scene_constructor: constructor of the scene class
    # - scene_constructor_kwargs: kwargs for the scene constructor
    # - scene_modifier: function to modify the scene after loading
    SCENE_KWARGS: dict = {
        'scene_constructor': Landsat.from_usgs,
        'scene_constructor_kwargs': {
            'band_selection': ['green', 'red', 'nir08'],
            'read_qa': True,
            'apply_scaling': False},
        'scene_modifier': preprocess_sentinel2_scene
    }


class LandsatC2L2Constants(Constants):
    """Constants for Landsat Collection 2 Level 2 scenes."""
    # name of the collection to query (Sentinel-2)
    COLLECTION: str = 'landsat-c2-l2'

    # filters to apply to the metadata
    # - only scenes with less than 80% cloudy pixels
    # - only scenes with processing level 'Level-2A'
    METADATA_FILTERS: list[Filter] = [
        Filter('eo:cloud_cover', '<', 80)
    ]

    # kwargs for the scene constructor
    # - scene_constructor: constructor of the scene class
    # - scene_constructor_kwargs: kwargs for the scene constructor
    # - scene_modifier: function to modify the scene after loading
    SCENE_KWARGS: dict = {
        'scene_constructor': Landsat.from_usgs,
        'scene_constructor_kwargs': {
            'band_selection': ['blue', 'green', 'red', 'nir08'],
            'read_qa': True,
            'apply_scaling': False},
        'scene_modifier': preprocess_landsat_scene
    }


class Sentinel2Constants(Constants):
    """Constants for Sentinel-2 scenes."""
    # name of the collection to query (Sentinel-2)
    COLLECTION: str = 'sentinel2-msi'

    # filters to apply to the metadata
    # - only scenes with less than 80% cloudy pixels
    # - only scenes with processing level 'Level-2A'
    METADATA_FILTERS: list[Filter] = [
        Filter('cloudy_pixel_percentage', '<', 80),
        Filter('processing_level', '==', 'Level-2A')
    ]

    # kwargs for the scene constructor
    # - scene_constructor: constructor of the scene class
    # - scene_constructor_kwargs: kwargs for the scene constructor
    # - scene_modifier: function to modify the scene after loading
    SCENE_KWARGS: dict = {
        'scene_constructor': Sentinel2.from_safe,
        'scene_constructor_kwargs': {
            'band_selection': ['B02', 'B03', 'B04', 'B08'],
            'read_scl': True,
            'apply_scaling': False},
        'scene_modifier': preprocess_sentinel2_scene
    }

    # name of spectral bands in the LUT
    BANDSELECTION_LUT = ['B02', 'B03', 'B04', 'B08']

    # spectral response function
    FPATH_SRF = 'https://raw.githubusercontent.com/EOA-team/sentinel2_crop_trait_timeseries/main/data/auxiliary/S2-SRF_COPE-GSEG-EOPG-TN-15-0007_3.1.xlsx'  # noqa E501
