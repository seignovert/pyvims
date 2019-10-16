"""Create geocube."""

import os
from datetime import datetime as dt

import numpy as np

from ..vectors import deg180


def _header(cube):
    """Geocube header.

    Parameters
    ----------
    cube: pyvims.VIMS
        VIMS cube.

    """
    return f"""
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;                                                                        ;
;  CASSINI/VIMS GEOCUBE                                                  ;
;    layer n°0 : Pixel central longitude projected on the surface (degE) ;
;          n°1 : Pixel central latitude projected on the surface (degN)  ;
;          n°2 : Incidence angle (sun/surface normal)                    ;
;          n°3 : Emergence angle (cassini/surface normal)                ;
;          n°4 : Phase angle (cassini/surface/sun)                       ;
;          n°5-8 : 4 corners longitudes projected on the surface (degE)  ;
;          n°9-12 : 4 corners latitudes projected on the surface (degN)  ;
;          n°13 : Distance cassini/surface (km)                          ;
;          n°14 : Spatial resolution in sample direction (km/pixel)      ;
;          n°15 : Altitude limb/surface (km)                             ;
;          n°16 : Limb pixel projected longitude (degE)                  ;
;          n°17 : Limb pixel projected latitude (degN)                   ;
;          n°18 : Limb pixel illumination angle                          ;
;          n°19 : Limb pixel emission angle                              ;
;          n°20 : Limb pixel phase angle                                 ;
;          n°21 : EMPTY                                                  ;
;                                                                        ;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


##############
#   HEADER   #
##############

Cube VIMS:
{cube.fname}

{cube.isis.dumps_header()}

"""[1:].encode()  # Discard the first line return


def _hdr(NS, NL, offset):
    """ENVI header file.

    Parameters
    ----------
    NS: int
        Number of samples.
    NL: int
        Number of lines.
    offset: int
        Header size.

    Raises
    ------
    ValueError
        If :py:attr:`offset` is invalid (``< 1``).

    """
    if offset < 1:
        raise ValueError('NAV file offset invalid')

    now = dt.now().strftime('%a %b %d %H:%M:%S %Y')

    return f'''ENVI
description = {{
  ENVI File, Created [{now}]}}
samples = {NS}
lines   = {NL}
bands   = 22
header offset = {offset}
file type = ENVI Standard
data type = 4
interleave = bsq
sensor type = Unknown
byte order = 0
wavelength units = Unknown
band names = {{
 n1: Pixel central longitude projected on the surface (degE),
 n2: Pixel central latitude projected on the surface (degN),
 n3: Incidence angle (sun/surface normal),
 n4: Emergence angle (cassini/surface normal),
 n5: Phase angle (cassini/surface/sun),
 n6: Longitude of the top-left pixel corner projected on the surface (degE),
 n7: Longitude of the top-right pixel corner projected on the surface (degE),
 n8: Longitude of the bottom-right pixel corner projected on the surface (degE),
 n9: Longitude of the bottom-left pixel corner projected on the surface (degE),
 n10: Latitude of the top-left pixel corner projected on the surface (degN),
 n11: Latitude of the top-right pixel corner projected on the surface (degN),
 n12: Latitude of the bottom-right pixel corner projected on the surface (degN),
 n13: Latitude of the bottom-left pixel corner projected on the surface (degN),
 n14: Distance cassini/surface (km),
 n15: Spatial resolution in sample direction (km/pixel),
 n16: Altitude limb/surface (km),
 n17: Limb pixel projected longitude (degE),
 n18: Limb pixel projected latitude (degN),
 n19: Limb pixel illumination angle,
 n20: Limb pixel emission angle,
 n21: Limb pixel phase angle,
 n22: EMPTY.}}
'''.encode()


def _mask(data, mask, fill=-99999):
    """Mask, fill and reshape data array.

    Parameters
    ----------
    data: np.array
        Data array to mask.
    mask: np.array
        Mask array.
    fill: int or float, optional
        Fill data array.

    """
    return np.ma.array(data,
                       mask=mask,
                       fill_value=fill,
                       dtype=np.float32
                       ).filled().copy(order='C')


def create_nav(cube, root=None):
    """Create a NAV geocube based on a ISIS VIMS cube.

    Parameters
    ----------
    cube: pyvims.VIMS
        VIMS cube to export.
    root: str, optional
        Export root folder.

    """
    fname = f'V{cube}_{cube.channel}'

    if root is None:
        root = cube.root

    nav_file = os.path.join(root, f'{fname}.nav')
    hdr_file = os.path.join(root, f'{fname}.hdr')

    limb = cube.limb
    ground = cube.ground
    corners = cube.rlonlat

    with open(nav_file, 'wb') as f:
        f.write(_header(cube))
        f.write(_mask(cube.lon_e, limb))
        f.write(_mask(cube.lat, limb))
        f.write(_mask(cube.inc, limb))
        f.write(_mask(cube.eme, limb))
        f.write(_mask(cube.phase, limb))
        for i in range(4):
            f.write(_mask(deg180(-corners[0, :, :, i]), limb))
        for i in range(4):
            f.write(_mask(corners[1, :, :, i], limb))
        f.write(_mask(cube.dist_sc, limb))
        f.write(_mask(cube.res_s, limb))
        f.write(_mask(cube.alt, ground))
        f.write(_mask(cube.lon_e, ground))
        f.write(_mask(cube.lat, ground))
        f.write(_mask(cube.inc, ground))
        f.write(_mask(cube.eme, ground))
        f.write(_mask(cube.phase, ground))
        f.write(_mask(np.zeros((cube.NL, cube.NS)), limb | ground))

    # Header offset
    offset = os.path.getsize(nav_file) - 22 * cube.NL * cube.NS * 4

    with open(hdr_file, 'wb') as f:
        f.write(_hdr(NS=cube.NS, NL=cube.NL, offset=offset))
