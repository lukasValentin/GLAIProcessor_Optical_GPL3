"""
Invert the RTM to get the canopy parameters from the reflectance
values.

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

import numpy as np
import pandas as pd

from eodal.core.band import Band
from eodal.core.raster import RasterCollection
from pathlib import Path
from rtm_inv.core.inversion import inv_img, retrieve_traits


def invert(
        fpath_lut: Path,
        fpath_srf: Path,
        output_dir: Path,
        band_selection_lut: list[str],
        band_selection_srf: list[str],
        traits: list[str],
        n_solutions: int = 10,
        cost_function: str = 'rmse'
) -> None:
    """
    Invert the RTM to get the canopy parameters from the reflectance
    values.

    :param fpath_lut:
        path to the lookup-table with simulated reflectance values
    :param fpath_srf:
        path to the COG containing the spectral values from the
        satellite
    :param output_dir:
        directory where the output will be saved
    :param band_selection_lut:
        list of band names to be used from the lookup-table
    :param band_selection_srf:
        list of band names to be used from the satellite data
    :param traits:
        list of trait names to be retrieved from the lookup-table
    :param n_solutions:
        number of solutions to be retrieved from the lookup-table.
        Default: 10.
    :param cost_function:
        cost function to be used for the inversion. Default: 'rmse'.
    """
    # make sure the two band selections have the same length
    assert len(band_selection_lut) == len(band_selection_srf)

    # read the lookup-table
    lut = pd.read_pickle(fpath_lut)
    if not set(band_selection_lut).issubset(lut.columns):
        raise KeyError(
            f'{band_selection_lut} not found in {fpath_lut}')

    # get the satellite spectral data as numpy array
    srf = RasterCollection.from_multi_band_raster(fpath_srf)
    # get GeoInfo of the first selected band for writing the output
    geo_info = srf[band_selection_srf[0]].geo_info

    # get the nodata value to allow proper masking
    # in the inversion process
    nodata = srf[srf.band_names[0]].nodata

    # scale data to correct physical units
    srf.scale(
        pixel_values_to_ignore=[nodata],  # important to ignore nodata!
        inplace=True)

    # mask nodata pixels. For nodata pixels, the inversion
    # makes no sense.
    srf.mask(
        mask=srf.band_names[0],
        mask_values=nodata,
        inplace=True
    )

    # get reflectance values as numpy ndarray
    try:
        srf = srf.get_values(
            band_selection=band_selection_srf)
    except Exception as e:
        raise KeyError from e

    # check if the satellite data is masked
    if isinstance(srf, np.ma.MaskedArray):
        mask = srf.mask[0, :, :]
        srf = srf.data
    else:
        mask = np.zeros(shape=(srf.shape[1], srf.shape[2]), dtype='uint8')
        mask = mask.astype('bool')

    # make sure the mask also captures all nodata pixels
    mask[srf[0, :, :] == nodata] = True

    # get the spectral values from the lookup-table
    lut_spectra = lut[band_selection_lut].values

    # invert the RTM
    lut_idxs, cost_function_values = inv_img(
        lut=lut_spectra,
        img=srf,
        mask=mask,
        cost_function=cost_function,
        n_solutions=n_solutions,
    )
    # debug: nodata handling makes no sense
    trait_img = retrieve_traits(
        lut=lut,
        lut_idxs=lut_idxs,
        traits=traits,
        cost_function_values=cost_function_values,
        measure='median'
    )
    trait_img = trait_img[0]

    # save traits to file
    trait_collection = RasterCollection()
    for tdx, trait in enumerate(traits):
        # TODO: We should also scale the traits to UINT16 to save
        # disk space
        trait_collection.add_band(
            Band,
            geo_info=geo_info,
            band_name=trait,
            values=trait_img[tdx, :, :],
            nodata=0
        )
    fpath_traits = output_dir / fpath_srf.name.replace('.tiff', '_traits.tiff')
    trait_collection.to_rasterio(fpath_traits, as_cog=True)
