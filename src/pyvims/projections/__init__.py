"""Projections module.

Mapping (old) projection are based on:

    * Snyder, J. (1987) “Map Projection - A Working Manual.”
        U. S. Geological Survey Professional Paper 1395.
        https://pubs.usgs.gov/pp/1395/report.pdf.

New projection are based on PROJ project:

    * https://proj.org/

"""

# Old projection methods
# New projections
from .equi import Equirectangular
from .equi_gc import Equirectangular as EquirectangularGC
from .equirectangular import equi_cube
from .globe import globe
from .img import bg_pole, index
from .mollweide import Mollweide
from .ortho import Orthographic
from .orthographic import ortho_cube, ortho_proj
from .path3d import Path3D
from .polar import polar_cube
from .sky import Sky
from .sky_old import sky_cube
from .stere import Stereographic


__all__ = [
    'Equirectangular',
    'EquirectangularGC',
    'Mollweide',
    'Orthographic',
    'Sky',
    'Stereographic',
    'Path3D',
    'bg_pole',
    'ortho_proj',
    'ortho_cube',
    'equi_cube',
    'globe',
    'index',
    'polar_cube',
    'sky_cube',
]
