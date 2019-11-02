"""PDS variables module."""

import os


RELEASES_URL = 'https://pds-imaging.jpl.nasa.gov/volumes'

ROOT_DATA = os.path.join(os.path.dirname(__file__), 'data')

# Create ROOT_DATA folder if not exists
_ = True if os.path.isdir(ROOT_DATA) else os.makedirs(ROOT_DATA)
