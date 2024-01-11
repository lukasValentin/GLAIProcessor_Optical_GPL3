"""
Test of the entire GLAI processor (integration test).
"""

import pytest
import shutil

from datetime import datetime
from eodal.mapper.feature import Feature
from pathlib import Path
from shapely.geometry import box

from glai_processor import monitor_folder


@pytest.fixture
def generate_test_feature() -> Feature:
    """get a test feature"""
    minx = 1252439
    miny = 6104370
    maxx = 1255556
    maxy = 6107113
    geom = box(minx, miny, maxx, maxy)
    feature = Feature(
        name='Upper Bavaria',
        geometry=geom,
        epsg=3857
    )
    return feature


def test_s2_pipeline(generate_test_feature):
    """test the pipeline end to end for Sentinel-2"""

    # output directory
    folder_to_monitor = Path('data/pipeline')
    # clean start with empty folder
    if folder_to_monitor.exists():
        shutil.rmtree(folder_to_monitor)
    folder_to_monitor.mkdir()

    # generate a test feature
    feature = generate_test_feature

    # time period
    time_start = datetime(2023, 6, 1)
    time_end = datetime(2023, 6, 10)

    # inversion setup
    rtm_params = 'https://raw.githubusercontent.com/EOA-team/sentinel2_crop_trait_timeseries/main/src/lut_params/prosail_danner-etal_all_phases.csv'  # noqa
    lut_size = 1000
    n_solutions = 200
    sampling_method = 'frs'
    traits = ['lai', 'cab']

    inversion_kwargs = {
        'rtm_params': rtm_params,
        'lut_size': lut_size,
        'n_solutions': n_solutions,
        'sampling_method': sampling_method,
        'traits': traits
    }

    monitor_folder(
        folder_to_monitor=folder_to_monitor,
        feature=feature,
        inversion_kwargs=inversion_kwargs,
        time_start=time_start,
        time_end=time_end,
    )

    # make sure all outputs have been generated
    assert folder_to_monitor.joinpath('latest_scene').exists()
    lut_files = [x for x in folder_to_monitor.glob('*.pkl')]
    tiff_files = [x for x in folder_to_monitor.glob('*.tiff')]
    angle_files = [x for x in folder_to_monitor.glob('*angles.yaml')]
    assert len(lut_files) == 4
    assert len(tiff_files) == 8
    assert len(angle_files) == 4
