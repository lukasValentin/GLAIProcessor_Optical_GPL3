"""
Interface to fetch optical satellite data to run the GLAI
processor.
"""

import geopandas as gpd

from pathlib import Path
from datetime import datetime

from eodal.core.sensors import Sentinel2
from eodal.core.sensors import Landsat
from eodal.mapper.filter import Filter
from eodal.mapper.feature import Feature
from eodal.mapper.mapper import Mapper, MapperConfigs


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
    ds: Sentinel2,
    target_resolution: int = 10,
) -> Sentinel2:
    """
    Resample a Sentinel-2 scene and mask clouds, shadows, and snow
    based on the Scene Classification Layer (SCL).

    :param target_resolution:
        spatial target resolution to resample all bands to.
    :returns:
        resampled, cloud-masked Sentinel-2 scene.
    """
    # resample scene
    ds.resample(inplace=True, target_resolution=target_resolution)
    # mask clouds, shadows, and snow
    ds.mask_clouds_and_shadows(inplace=True)
    return ds


def fetch_data(
        mapper_configs: MapperConfigs,
        output_dir: Path,
        scene_kwargs: dict = None,
        band_selection: list[str] = ['red', 'green', 'blue', 'nir_1']
) -> None:
    """
    Fetch satellite data from STAC API.

    Parameters
    ----------
    mapper_configs : MapperConfigs
        MapperConfigs object.
    output_dir : Path
        Output directory to save data to.
    """
    # query the scenes available (no I/O of scenes, this only fetches metadata)
    mapper = Mapper(mapper_configs)
    mapper.query_scenes()

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

    # to enhance reproducibility and provide proper documentation, the
    # MapperConfigs are saved as yaml (and can be loaded again from yaml)
    fpath_mapper_configs = output_dir.joinpath(
        f'{mapper_configs.collection}_{mapper_configs.time_start.date()}-' +
        f'{mapper_configs.time_end.date()}_mapper_configs.yaml'
    )
    mapper_configs.to_yaml(fpath_mapper_configs)
