PyVIMS
======

|Build| |Conda| |PyPI| |Python| |Status| |Version| |Binder| |License|

.. |Build| image:: https://travis-ci.org/seignovert/pyvims.svg?branch=master
        :target: https://travis-ci.org/seignovert/pyvims
.. |Conda| image:: https://img.shields.io/badge/conda|seignovert-pyvims-blue.svg?logo=python&logoColor=white
        :target: https://anaconda.org/seignovert/pyvims
.. |PyPI| image:: https://img.shields.io/badge/PyPI-pyvims-blue.svg?logo=python&logoColor=white
        :target: https://pypi.org/project/pyvims
.. |Python| image:: https://img.shields.io/pypi/pyversions/pyvims.svg?label=Python
        :target: https://pypi.org/project/pyvims
.. |Status| image:: https://img.shields.io/pypi/status/pyvims.svg?label=Status
        :target: https://pypi.org/project/pyvims
.. |Version| image:: https://img.shields.io/pypi/v/pyvims.svg?label=Version
        :target: https://pypi.org/project/pyvims
.. |Binder| image:: https://badgen.net/badge/Binder/Live%20Demo/blue?icon=terminal
        :target: https://mybinder.org/v2/gh/seignovert/pyvims/master?filepath=playground.ipynb
.. |License| image:: https://img.shields.io/pypi/l/pyvims.svg?label=License
        :target: https://pypi.org/project/pyvims


Python package to manipulate the Cassini VIMS data.


Install
-------

With ``conda``
~~~~~~~~~~~~~~

Add conda-forge channel:

.. code:: bash

    $ conda config --add channels conda-forge

Install ``pyvims`` package:

.. code:: bash

    $ conda install -c seignovert pyvims


With ``pip``
~~~~~~~~~~~~

This module use ``OpenCV``, ``GDAL`` and ``Basemap`` libraries.
Depending on your operating system you need to install them first.
In python you should be able to do:

.. code:: python

    >>> import cv2
    >>> import osgeo
    >>> from mpl_toolkits.basemap import Basemap

Then you can install ``pyvims``

.. code:: bash

    $ pip install pyvims


Examples
--------
Download test files (ISIS3 cubes of ``1487096932_1``):

.. code:: bash

    $ wget -O C1487096932_1_vis.cub https://vims.univ-nantes.fr/vis/cal/1487096932_1
    $ wget -O C1487096932_1_ir.cub https://vims.univ-nantes.fr/ir/cal/1487096932_1
    $ wget -O N1487096932_1_vis.cub https://vims.univ-nantes.fr/vis/nav/1487096932_1
    $ wget -O N1487096932_1_ir.cub https://vims.univ-nantes.fr/ir/nav/1487096932_1

To use, simply do:

.. code:: python

    >>> from pyvims import VIMS

    >>> cub = VIMS('1487096932_1')

    >>> cub
    VIMS cube: 1487096932_1 [ISIS3]

    >>> cub.time
    '2005-02-14T18:05:00.976500'

    >>> cub.target
    u'TITAN'

    >>> cub.NS, cub.NL
    (42, 42)

For more details, take a look to the
`static Jupyter NoteBook <https://nbviewer.jupyter.org/github/seignovert/pyvims/blob/master/pyvims.ipynb>`_
where more examples of usage are provided. You can also try this
`live demo on Binder <https://mybinder.org/v2/gh/seignovert/pyvims/master?filepath=playground.ipynb>`_.


Disclaimer
----------
This project is not supported or endorsed by either JPL, NAIF or NASA. The code is provided "as is", use at your own risk.
