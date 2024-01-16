'''
Run the PROSAIL RTM forward model to generate a lookup-table
for the given sensor and angles.

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
'''

from datetime import datetime, timedelta
from pathlib import Path


PLATFORMS = {'S2A': 'Sentinel2A', 'S2B': 'Sentinel2B'}


def get_latest_scene(output_dir: Path, start_time: datetime) -> datetime:
    """
    Get the timestamp of the latest scene from a
    file called `latest_scene`. If this file does
    not exist use the default date

    :param output_dir:
        directory where scenes are stored (in sub-directories)
    :param constants:
        constants object
    """
    fpath_latest_scene = output_dir.joinpath('latest_scene')
    if fpath_latest_scene.exists():
        with open(output_dir.joinpath('latest_scene'), 'r') as f:
            timestamp_raw = f.read()
        timestamp_raw = timestamp_raw.replace('\n', '')
        timestamp = datetime.strptime(timestamp_raw, '%Y-%m-%d')
    else:
        timestamp = start_time - timedelta(days=1)
    return timestamp


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


def indicate_complete(output_dir_scene: Path) -> None:
    """
    Indicate that a scene was extracted and post-
    processed complete by writing a file named
    "complete" to the scene sub-directory.

    :param output_dir_scene:
        output directory of the scene.
    """
    fpath_complete = output_dir_scene.joinpath(
        'complete.txt'
    )
    with open(fpath_complete, 'w') as f:
        f.write('complete')


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


def set_latest_scene(
        output_dir: Path,
        timestamp: datetime
) -> None:
    """
    Set the timestamp of the latest scene
    to a file called `latest_scene`.

    :param output_dir:
        directory where scenes are stored (in sub-directories)
    :param timestamp:
        time stamp of the latest scene
    """
    # make sure the latest scene is never in the future
    if timestamp > datetime.now():
        timestamp = datetime.now()
    # create output directory if it does not exist
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
    with open(output_dir.joinpath('latest_scene'), 'w+') as f:
        f.write(f'{timestamp.date()}')
