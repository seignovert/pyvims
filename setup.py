# This will try to import setuptools. If not here, it fails with a message
try:
    from setuptools import setup
except ImportError:
    raise ImportError("PyVIMS could not be installed, probably because"
        " setuptools is not installed on this computer."
        "\nInstall ez_setup ([sudo] pip install ez_setup) and try again.")

setup(name='pyvims',
      version='0.1',
      description='Python package to manipulate the Cassini VIMS data.',
      url='http://github.com/seignovert/pyvims',
      author='Benoit Seignovert',
      author_email='pyvims@seignovert.fr',
      license='MIT',
      packages=['pyvims'],
      install_requires=[
          'numpy',
          'datetime',
          'opencv-python',
          'piexif',
          'geojson',
          'spiceypy',
      ],
      dependency_links=[
          'https://github.com/seignovert/pvl/tarball/master#egg=package-1.0',
          'https://github.com/seignovert/planetaryimage/tarball/master#egg=package-1.0',
      ],
      zip_safe=False)
