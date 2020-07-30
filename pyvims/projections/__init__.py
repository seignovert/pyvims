"""Projections module.

Mapping (old) projection are based on:

    * Snyder, J. (1987) “Map Projection - A Working Manual.”
        U. S. Geological Survey Professional Paper 1395.
        https://pubs.usgs.gov/pp/1395/report.pdf.

New projection are based on PROJ project:

    * https://proj.org/

"""

# Old projection methods
from .equirectangular import equi_cube
from .orthographic import ortho_cube, ortho_proj
from .polar import polar_cube
from .sky_old import sky_cube
# New projections
from .equi import Equirectangular
from .equi_gc import Equirectangular as EquirectangularGC
from .mollweide import Mollweide
from .ortho import Orthographic
from .sky import Sky
from .stere import Stereographic
from .globe import globe
from .path3d import Path3D
from .img import index, bg_pole


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
