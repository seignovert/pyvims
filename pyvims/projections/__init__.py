"""VIMS projections module.

Mapping projection are based on :

    * Snyder, J. (1987) “Map Projection - A Working Manual.”
        U. S. Geological Survey Professional Paper 1395.
        https://pubs.usgs.gov/pp/1395/report.pdf.

"""

# Old projection methods
from .equirectangular import equi_cube
from .orthographic import ortho_proj, ortho_cube
from .polar import polar_cube
from .sky import sky_cube

# New projections
from .equi import Equirectangular
from .stere import Stereographic


__all__ = [
    'Equirectangular',
    'Stereographic',
    'ortho_proj',
    'ortho_cube',
    'equi_cube',
    'polar_cube',
    'sky_cube',
]
