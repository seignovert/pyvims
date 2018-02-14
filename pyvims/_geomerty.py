# -*- coding: utf-8 -*-
import os
import numpy as np

def circle3pts(a, b, c):
    '''[3D circle through 3 points a/b/c](https: // math.stackexchange.com/a/2009402)'''
    ax, ay, az = a
    bx, by, bz = b
    cx, cy, cz = c

    Cx = bx-ax
    Cy = by-ay
    Cz = bz-az
    Bx = cx-ax
    By = cy-ay
    Bz = cz-az
    B2 = ax**2-cx**2+ay**2-cy**2+az**2-cz**2
    C2 = ax**2-bx**2+ay**2-by**2+az**2-bz**2

    CByz = Cy*Bz-Cz*By
    CBxz = Cx*Bz-Cz*Bx
    CBxy = Cx*By-Cy*Bx
    ZZ1 = -(Bz-Cz*Bx/Cx)/(By-Cy*Bx/Cx)
    Z01 = -(B2-Bx/Cx*C2)/(2*(By-Cy*Bx/Cx))
    ZZ2 = -(ZZ1*Cy+Cz)/Cx
    Z02 = -(2*Z01*Cy+C2)/(2*Cx)

    dz = -((Z02-ax)*CByz-(Z01-ay)*CBxz-az*CBxy)/(ZZ2*CByz-ZZ1*CBxz+CBxy)
    dx = ZZ2*dz + Z02
    dy = ZZ1*dz + Z01

    r = np.sqrt((ax-dx)**2 + (ay-dy)**2 + (az-dz)**2)

    return np.array([dx, dy, dz]), r

class BODY_SPHERE(object):
    '''Circle projected on a body sphere'''
    def __init__(self, R_body):
        self.r = R_body
        return

    def __repr__(self):
        return 'Circle on a Sphere'

    def lonlat(self, xyz):
        '''Convert cartesian coordinates to Longitude [West] and Latitude [North]'''
        lon = np.degrees(np.arctan2(xyz[1], xyz[0]))
        lat = np.degrees(np.arcsin(xyz[2] / np.sqrt(np.sum(xyz**2, 0))))
        return lon, lat

    def xyz(self, lon, lat):
        x = self.r * np.cos(np.radians(lon)) * np.cos(np.radians(lat))
        y = self.r * np.sin(np.radians(lon)) * np.cos(np.radians(lat))
        z = self.r * np.sin(np.radians(lat))
        return np.array([x, y, z])

    def circle(self, Rc, Ra, lon=0, lat=0, npt=100):
        '''Longitude and Latitude of circle on a sphere'''
        # Circle angular parameter
        theta = np.radians(np.arange(0, 360, 360/npt))

        # Circle centered on the X-axis with `r` radius
        xyz = np.array([
            Rc + 0*theta,
            Ra * np.cos(-theta),
            Ra * np.sin(-theta)
        ])

        # Rotation matrix along the Y-axis
        clat = np.cos(np.radians(lat))
        slat = np.sin(np.radians(lat))
        Mlat = np.array([[clat, 0, -slat], [0, 1, 0], [slat, 0, clat]])

        # Rotation matrix along the Z-axis
        clon = np.cos(np.radians(lon))
        slon = np.sin(np.radians(lon))
        Mlon = np.array([[clon, -slon, 0], [slon, clon, 0], [0, 0, 1]])

        # Center the circle on SC point
        return self.lonlat(np.dot(Mlon, np.dot(Mlat, xyz)))

    def sun(self, SS_lon=0, SS_lat=0, npt=100):
        '''Longitude and Latitude of solar great circle'''
        return self.circle(0, self.r, lon=SS_lon, lat=SS_lat, npt=npt)

    def limb(self, dist, SC_lon=0, SC_lat=0, npt=100):
        '''Longitude and Latitude of limb circle'''
        # Radius distance of the circle center
        Rc = self.r**2 / dist
        # Apparent radius at distance `dist`
        Ra = self.r * np.sqrt(1 - (self.r/dist)**2)

        return self.circle(Rc, Ra, lon=SC_lon, lat=SC_lat, npt=npt)

    def ground(self, pts, npt=75):
        '''Longitude and Latitude of ground circle through 3 pts A/B/C'''
        a = self.xyz(pts[0][0], pts[0][1])
        b = self.xyz(pts[1][0], pts[1][1])
        c = self.xyz(pts[2][0], pts[2][1])
        d, Ra = circle3pts(a, b, c)

        Rc = np.sqrt(np.sum(d**2, 0))
        lon, lat = self.lonlat(d)

        return self.circle(Rc, Ra, lon=lon, lat=lat, npt=npt)

