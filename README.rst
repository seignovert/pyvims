.. image:: https://img.shields.io/pypi/status/pyvims.svg?label=Status
    :alt: PyPI - Status
.. image:: https://img.shields.io/pypi/v/pyvims.svg?label=Version
    :alt: PyPI - Version
.. image:: https://img.shields.io/pypi/pyversions/pyvims.svg?label=Python
    :alt: PyPI - Python Version
.. image:: https://img.shields.io/pypi/l/pyvims.svg?label=License
    :alt: PyPI - License

PyVIMS
======
Python package to manipulate the Cassini VIMS data.

Install
-------
With ``pip``:

.. code-block:: console

    pip install pyvims

With the ``source files``:

.. code-block:: console

    git clone https://github.com/seignovert/pyvims.git
    cd pyvims ; python setup.py install

Testing
-------
Check the install:

.. code:: python

    >>> from pyvims import VIMS

Examples
--------
Download test files (ISIS3 cubes of ``1487096932_1``):

.. code-block:: console

    wget https://vims.univ-nantes.fr/data/isis/T3/C1487096932_1_vis.cub
    wget https://vims.univ-nantes.fr/data/isis/T3/C1487096932_1_ir.cub
    wget https://vims.univ-nantes.fr/data/isis/T3/N1487096932_1_vis.cub
    wget https://vims.univ-nantes.fr/data/isis/T3/N1487096932_1_ir.cub

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

Dependencies
------------
- Numpy
- DateTime
- CV2
- Piexif
- PVL_ (`patched issue #34 <https://github.com/planetarypy/pvl/pull/34>`_)
- PlanetaryImage
- SpiceyPy

.. _PVL: https://github.com/seignovert/pvl
