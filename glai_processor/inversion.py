"""
Invert the RTM to get the canopy parameters from the reflectance
values.
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
        n_solutions: int = 1,
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
        number of solutions to be retrieved from the lookup-table
    :param cost_function:
        cost function to be used for the inversion
    """
    # make sure the two band selections have the same length
    assert len(band_selection_lut) == len(band_selection_srf)

    # read the lookup-table
    lut = pd.read_pickle(fpath_lut)

    # get the satellite spectral data as numpy array
    srf = RasterCollection.from_multiband_raster(fpath_srf)
    srf.scale_values(inplace=True)
    srf = srf.get_values(band_selection=band_selection_srf)

    # check if the satellite data is masked
    if isinstance(srf, np.ma.MaskedArray):
        mask = srf.mask[0, :, :]
        srf = srf.data
    else:
        mask = np.zeros(shape=(srf.shape[1], srf.shape[2]), dtype='uint8')
        mask = mask.as_type('bool')

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
    trait_img = retrieve_traits(
        lut=lut,
        lut_idxs=lut_idxs,
        traits=traits,
        cost_function_values=cost_function_values,
        measure='median'
    )

    # save traits to file
    trait_collection = RasterCollection()
    for tdx, trait in enumerate(traits):
        trait_collection.add_band(
            Band,
            geo_info=srf[band_selection_srf[0]].geo_info,
            band_name=trait,
            values=trait_img[tdx, :, :]
        )
    fpath_traits = output_dir / fpath_srf.name.replace('.tiff', '_traits.tiff')
    trait_collection.to_rasterio(fpath_traits, as_cog=True)
