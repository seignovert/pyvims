PyVIMS
======

|Build| |Python| |Status| |Version| |License|

|Conda| |PyPI| |Docker| |Binder|

.. |Build| image:: https://travis-ci.org/seignovert/pyvims.svg?branch=master
        :target: https://travis-ci.org/seignovert/pyvims
.. |Python| image:: https://img.shields.io/pypi/pyversions/pyvims.svg?label=Python
        :target: https://pypi.org/project/pyvims
.. |Status| image:: https://img.shields.io/pypi/status/pyvims.svg?label=Status
        :target: https://pypi.org/project/pyvims
.. |Version| image:: https://img.shields.io/pypi/v/pyvims.svg?label=Version
        :target: https://pypi.org/project/pyvims
.. |License| image:: https://img.shields.io/pypi/l/pyvims.svg?label=License
        :target: https://pypi.org/project/pyvims
.. |Conda| image:: https://img.shields.io/badge/conda|seignovert-pyvims-blue.svg?logo=python&logoColor=white
        :target: https://anaconda.org/seignovert/pyvims
.. |PyPI| image:: https://img.shields.io/badge/PyPI-pyvims-blue.svg?logo=python&logoColor=white
        :target: https://pypi.org/project/pyvims
.. |Docker| image:: https://badgen.net/badge/docker|seignovert/pyvims/blue?icon=docker
        :target: https://hub.docker.com/r/seignovert/pyvims
.. |Binder| image:: https://badgen.net/badge/Binder/Live%20Demo/blue?icon=terminal
        :target: https://mybinder.org/v2/gh/seignovert/pyvims/dev?filepath=notebooks/playground.ipynb


Python package to manipulate the Cassini VIMS data.


Install
-------

From the sources
~~~~~~~~~~~~~~~~

If `pyvims` was already install, it is recommended to create a new
python environnement. For example with conda:


.. code:: bash

    conda create -n pyvims-dev python=3.6
    conda activate pyvims-dev

Then clone the sources from the `dev` branch and install them
in `develop` mode.

.. code:: bash

    git clone -b dev https://github.com/seignovert/pyvims.git
    cd pyvims
    python setup.py develop


With ``pip``
~~~~~~~~~~~~

**Not available yet…** (use the `master` branch if needed)

With ``conda``
~~~~~~~~~~~~~~

**Not available yet…** (use the `master` branch if needed)


With ``docker``
~~~~~~~~~~~~~~~

**Not available yet…** (use the `master` branch if needed)

Examples
--------
To use, simply do:

.. code:: python

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

    >>> cub.time
    datetime.datetime(2005, 2, 14, 18, 5, 0, 976500)

    >>> cube.target_name
    'TITAN'

    >>> cube.NS, cube.NL
    (42, 42)

For more details, take a look to the
`static Jupyter NoteBook <https://nbviewer.jupyter.org/github/seignovert/pyvims/blob/dev/notebooks/pyvims.ipynb>`_
where more examples of usage are provided. You can also try this
`live demo on Binder <https://mybinder.org/v2/gh/seignovert/pyvims/dev?filepath=notebooks/playground.ipynb>`_.


Disclaimer
----------
This project is not supported or endorsed by either JPL, NAIF or NASA.
The code is provided "as is", use at your own risk.
