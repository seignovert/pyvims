# PyVIMS

[![Build](https://github.com/seignovert/pyvims/workflows/Github%20Actions/badge.svg)](https://github.com/seignovert/pyvims/actions?query=workflow%3AGithub%20Actions)
[![Python](https://img.shields.io/pypi/pyversions/pyvims.svg?label=Python)](https://pypi.org/project/pyvims)
[![Status](https://img.shields.io/pypi/status/pyvims.svg?label=Status)](https://pypi.org/project/pyvims)
[![Version](https://img.shields.io/pypi/v/pyvims.svg?label=Version)](https://pypi.org/project/pyvims)
[![License](https://img.shields.io/pypi/l/pyvims.svg?label=License)](https://pypi.org/project/pyvims)

[![PyPI](https://img.shields.io/badge/PyPI-pyvims-blue.svg?logo=python&logoColor=white)](https://pypi.org/project/pyvims)
[![Conda-Forge](https://img.shields.io/badge/conda--forge-pyvims-blue.svg?logo=condaforge&logoColor=white)](https://anaconda.org/conda-forge/pyvims)
[![Binder](https://badgen.net/badge/Binder/Live%20Demo/blue?icon=terminal)](https://mybinder.org/v2/gh/seignovert/pyvims/main?filepath=notebooks/playground.ipynb)
[![Zenodo](https://zenodo.org/badge/126732857.svg)](https://zenodo.org/badge/latestdoi/126732857)

Python package to manipulate the Cassini VIMS data.

## Install

``` bash
pip install pyvims
```
PyVIMS is also distribute in [conda-forge](https://anaconda.org/conda-forge/pyvims).

## Get started

``` python
>>> from pyvims import VIMS

>>> cube = VIMS('1487096932_1')

>>> cube
<VIMS> Cube: 1487096932_1
- Size: (42, 42)
- Channel: IR
- Mode: NORMAL
- Start time: 2005-02-14 18:02:29.023000
- Stop time: 2005-02-14 18:07:32.930000
- Exposure: 0.16276 sec
- Duration: 0:05:03.907000
- Main target: TITAN
- Flyby: T3

>>> cube.time
datetime.datetime(2005, 2, 14, 18, 5, 0, 976500)

>>> cube.target_name
'TITAN'

>>> cube.NS, cube.NL
(42, 42)
```

For more details, take a look to the [static Jupyter
NoteBook](https://nbviewer.jupyter.org/github/seignovert/pyvims/blob/main/notebooks/pyvims.ipynb)
where more examples of usage are provided. You can also try this [live
demo on
Binder](https://mybinder.org/v2/gh/seignovert/pyvims/main?filepath=notebooks/playground.ipynb).

## Citation

If you use this package for your research, please cite it as:

> Seignovert et al. - PyVIMS (Version 1.0.5) -
> [Zenodo](https://zenodo.org/badge/latestdoi/126732857)

## Local development

This project is managed with [uv](https://docs.astral.sh/uv/).
If you want to contribute to this project, you need to install it first.
Then clone [this repo](https://github.com/seignovert/pyvims):

```bash
git clone https://github.com/seignovert/pyvims
cd pyvims
```

Lint the content of the project with `ruff`:
```bash
uv run ruff check
uv run ruff format
```

Check that all the tests pass successfully:
```bash
uv run pytest
uv run pytest --nbval-lax notebooks/
```

## Disclaimer

This project is distributed under BSD 3-Clause open-source license.
Don't forget to [cite this package](#citation) if you use it.
Note that this project is not supported or endorsed neither by JPL, NASA nor ESA.
The code is provided "as is", use at your own risk.
