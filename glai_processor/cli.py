"""
Command line interface for the GLAIProcessor.
"""

import argparse
import geopandas as gpd

from datetime import datetime
from eodal.mapper.feature import Feature
from pathlib import Path

from glai_processor.constants import *  # noqa
from glai_processor import monitor_folder


def get_parser() -> argparse.ArgumentParser:
    """
    Get the command line parser for the GLAIProcessor.
    """
    # parse the command line arguments
    parser = argparse.ArgumentParser(
        description='Green Leaf Area Index (GLAI) processor for optical satellite data.'  # noqa E501
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        help='Path to the output directory.',
        required=True
    )
    parser.add_argument(
        '--feature',
        type=str,
        help='Path to the geometry for which to retrieve GLAI (GeoPackage, Shapefile).',  # noqa E501
        required=True
    )
    parser.add_argument(
        '--time_start',
        type=str,
        help='Start date of the time period for which to retrieve GLAI.',
        required=True
    )
    parser.add_argument(
        '--time_end',
        type=str,
        help='End date of the time period for which to retrieve GLAI.',
        required=True
    )
    parser.add_argument(
        '--rtm_params',
        type=str,
        help='Path to the RTM parameter file (CSV).',
        default='https://raw.githubusercontent.com/EOA-team/sentinel2_crop_trait_timeseries/main/src/lut_params/prosail_danner-etal_all_phases.csv',  # noqa E501
        required=True
    )
    parser.add_argument(
        '--lut_size',
        type=int,
        help='Number of samples in the LUT. Default: 20000',
        default=20_000
    )
    parser.add_argument(
        '--n_solutions',
        type=int,
        help='Number of solutions to be sampled. Default: 1000',
        default=1_000
    )
    parser.add_argument(
        '--sampling_method',
        type=str,
        help='Sampling method for the inversion.',
        options=['frs', 'lhs'],
        default='frs'
    )
    parser.add_argument(
        '--traits',
        type=list[str],
        help='List of traits to retrieve.',
        options=[
            'n', 'lai', 'cab', 'car', 'cbrown',
            'cw', 'cm', 'ant', 'lidfa', 'lidfb',
            'hspot', 'rsoil', 'psoil', 'tts',
            'tto', 'psi'],
        default=['lai', 'cab']
    )
    parser.add_argument(
        '--platform',
        type=str,
        help='Satellite platform.',
        default='Sentinel2'
    )
    parser.add_argument(
        '--temporal_increment',
        type=int,
        help='Temporal increment in days.',
        default=7
    )

    return parser


def main() -> None:
    """
    Command line interface for the GLAIProcessor.
    """
    # get the command line arguments
    parser = get_parser()
    args = parser.parse_args()

    # convert the arguments
    output_dir = Path(args.output_dir)
    fpath_feature = Path(args.feature)
    feature = Feature.from_geoseries(
        gpd.read_file(fpath_feature).dissolve().geometry
    )
    time_start = datetime.strptime(args.time_start, '%Y-%m-%d')
    time_end = datetime.strptime(args.time_end, '%Y-%m-%d')
    rtm_params = args.rtm_params
    lut_size = args.lut_size
    n_solutions = args.n_solutions
    sampling_method = args.sampling_method
    traits = args.traits
    platform = args.platform
    constants = eval(f'{platform}Constants')
    temporal_increment = args.temporal_increment

    # run the GLAIProcessor
    monitor_folder(
        folder_to_monitor=output_dir,
        feature=feature,
        inversion_kwargs={
            'rtm_params': rtm_params,
            'lut_size': lut_size,
            'n_solutions': n_solutions,
            'sampling_method': sampling_method,
            'traits': traits
        },
        time_start=time_start,
        time_end=time_end,
        constants=constants,
        temporal_increment_days=temporal_increment
    )


if __name__ == '__main__':
    main()
