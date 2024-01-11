![Tests](https://github.com/terensis/GLAIProcessor_Optical_GPL3/actions/workflows/python-app.yml/badge.svg)
[![codecov](https://codecov.io/gh/terensis/GLAIProcessor_Optical_GPL3/graph/badge.svg?token=VFfwEUJmZT)](https://codecov.io/gh/terensis/GLAIProcessor_Optical_GPL3)

# Green Leaf Area Index Retrieval from Optical Data (and other traits)

This software enables the retrieval of bio-physical and bio-chemical plant traits from optical remote sensing data by inverting the [PROSAIL](http://teledetection.ipgp.jussieu.fr/prosail/) radiative transfer model (RTM). The main focus is on the [Green Leaf Area Index](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/leaf-area-index), which is among the most important functional canopy traits describing the accumulation of photosynthetically active biomass and, thus, the area available for material and energy fluxes between plants and the atmosphere.

The default setting of the package uses RTM inputs tailored to [winter wheat](https://en.wikipedia.org/wiki/Winter_wheat) in the [stem elongation period](http://corn.agronomy.wisc.edu/Crops/Wheat/L007.aspx) (BBCH growth stages 30 to 59) using calibration data from field phenotyping as described in [our peer-reviewed scientific article](https://doi.org/10.1016/j.rse.2023.113860).

This software is an improved version of the original source code for the paper of [Graf et al. (2023, RSE)](https://doi.org/10.1016/j.rse.2023.113860) available [GNU GENERAL PUBLIC LICENSE Version 3](/LICENSE) made available by [Terensis](https://ethz.ch/en/industry/entrepreneurship/find-offers-programs-space-grants-for-entrepreneurs/pioneer-fellowship/2023/terensis.html). See [here](https://github.com/EOA-team/sentinel2_crop_traits) for the original source code by [Lukas Valentin Graf](https://github.com/lukasValentin).

## Installation

From source:

```bash
git clone git@github.com:terensis/GLAIProcessor_Optical_GPL3.git
cd GLAIProcessor_Optical_GPL3
python setup.py install
```

From pypi:

```bash
pip install glai-processor
```

## Tests

Testing the package is done using [pytest](https://docs.pytest.org/en/7.4.x/). Run the following command in a terminal in the root of the repository:

```bash
python -m pytest tests
```

## License:

This software is made available under [GNU GENERAL PUBLIC LICENSE Version 3](/LICENSE).
