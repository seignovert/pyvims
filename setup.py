# This will try to import setuptools. If not here, it fails with a message
try:
    from setuptools import setup
except ImportError:
    raise ImportError("PyVIMS could not be installed, probably because"
        " setuptools is not installed on this computer."
        "\nInstall ez_setup ([sudo] pip install ez_setup) and try again.")

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyvims',
      version='0.1.3',
      description='Python package to manipulate the Cassini VIMS data.',
      long_description=readme(),
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.6',
          'Topic :: Scientific/Engineering :: Atmospheric Science',
          'Topic :: Scientific/Engineering :: Astronomy',
          'Intended Audience :: Science/Research',
      ],
      url='http://github.com/seignovert/pyvims',
      author='Benoit Seignovert',
      author_email='pyvims@seignovert.fr',
      license='MIT',
      keywords='nasa cassini vims titan',
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
      include_package_data=True,
      zip_safe=False)
