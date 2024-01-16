![Tests](https://github.com/terensis/GLAIProcessor_Optical_GPL3/actions/workflows/python-app.yml/badge.svg)
[![codecov](https://codecov.io/gh/terensis/GLAIProcessor_Optical_GPL3/graph/badge.svg?token=VFfwEUJmZT)](https://codecov.io/gh/terensis/GLAIProcessor_Optical_GPL3)

# Green Leaf Area Index Retrieval from Optical Data (and other traits)

This software enables the retrieval of bio-physical and bio-chemical plant traits from optical remote sensing data by inverting the [PROSAIL](http://teledetection.ipgp.jussieu.fr/prosail/) radiative transfer model (RTM). The main focus is on the [Green Leaf Area Index](https://www.sciencedirect.com/topics/agricultural-and-biological-sciences/leaf-area-index), which is among the most important functional canopy traits describing the accumulation of photosynthetically active biomass and, thus, the area available for material and energy fluxes between plants and the atmosphere.

The default setting of the package uses RTM inputs tailored to [winter wheat](https://en.wikipedia.org/wiki/Winter_wheat) using calibration data from field phenotyping as described in [our peer-reviewed scientific article](https://doi.org/10.1016/j.rse.2023.113860).

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

## Usage

### Command line interface

After installation, `glai_processor` can be called from the command line in the environment `glai_processor` was installed to.

```bash
$ glai_processor
usage: glai_processor [-h] --output_dir OUTPUT_DIR --feature FEATURE --time_start TIME_START --time_end TIME_END [--rtm_params RTM_PARAMS] [--lut_size LUT_SIZE]
                      [--n_solutions N_SOLUTIONS] [--sampling_method {frs,lhs}] [--traits {n,lai,cab,car,cbrown,cw,cm,ant,lidfa,lidfb,hspot,rsoil,psoil,tts,tto,psi}]
                      [--platform PLATFORM] [--temporal_increment TEMPORAL_INCREMENT]
glai_processor: error: the following arguments are required: --output_dir, --feature, --time_start, --time_end
```

A sample call (Linux) could look like

```bash
glai_processor --output_dir /home/$USER/GLAI_Test --feature https://github.com/terensis/GLAIProcessor_Optical_GPL3/raw/main/data/bbox_wtz.gpkg --time_start 2023-10-01 --time_end 2023-10-15
```
Here, a small bounding box of an agricultural area in Switzerland is queried, and Sentinel-2 data is extracted for a period of two weeks in October 2023. Subsequently, PROSAIL lookup-tables are generated for the Sentinel-2 scenes found and inversion is run to retrieve GLAI and the leaf chlorophyll a+b (cab) content. The output will be stored in a directory (`GLAI_Test`) in the user's home directory.

### Python

Of course, calling `glai_processor` from Python is possible, too. Run

```python
import glai_processor
```

to import it into your Python script.

## Tests

Testing the package is done using [pytest](https://docs.pytest.org/en/7.4.x/). Run the following command in a terminal in the root of the repository:

```bash
python -m pytest test
```

## License:

This software is made available under [GNU GENERAL PUBLIC LICENSE Version 3](/LICENSE).
