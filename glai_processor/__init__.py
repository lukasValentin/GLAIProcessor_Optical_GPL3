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

from glai_processor.fetch_satellite_data import fetch_data
from glai_processor.inversion import invert
from glai_processor.utils import (
    get_required_angles,
    FPATH_SRF,
    RTM_PARAMS,
    LUT_SIZE,
    SAMPLING_METHOD,
    PLATFORMS,
)

__all__ = [
    'fetch_satellite_data',
    'invert',
    'get_required_angles',
    'FPATH_SRF',
    'RTM_PARAMS',
    'LUT_SIZE',
    'SAMPLING_METHOD',
    'PLATFORMS',
]

# TODO: add a function to run the full pipeline
def run():
    pass
