"""PyVIMS setup."""

from pathlib import Path

from setuptools import find_packages, setup


HERE = Path(__file__).parent
README = (HERE / 'README.rst').read_text()
REQUIREMENTS = (HERE / 'requirements.txt').read_text().split()


setup(
    name='pyvims',
    version='1.0.3',
    description='Python package to manipulate the Cassini VIMS data',
    long_description=README,
    author='Benoit Seignovert (LPG-Nantes)',
    author_email='pyvims@seignovert.fr',
    url='https://github.com/seignovert/pyvims',
    license='BSD',
    keywords=['cassini', 'vims', 'titan'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Astronomy',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
    ],
    python_requires='>=3.6',
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=['binder', 'tests', 'notebooks']),
    include_package_data=True,
)
