"""Template setup file."""
import codecs
import os
from io import open as io_open

from setuptools import setup

# Use single source package versioning.  Follows:
# https://packaging.python.org/guides/single-sourcing-package-version/
#
# With this approach, we can include the version within the setup file
# while at the same time allowing the user to print the version from
# the module
HERE = os.path.abspath(os.path.dirname(__file__))
__version__ = None
version_file = os.path.join(HERE, 'ansys', 'pyoptics', 'speos', '_version.py')
with io_open(version_file, mode='r') as fd:
    exec(fd.read())


# Get the long description from the README file
# This is needed for the description on PyPI
def read(rel_path):
    with codecs.open(os.path.join(HERE, rel_path), 'r') as fp:
        return fp.read()


with open(os.path.join(HERE, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='ansys-pyoptics-speos',
    packages=['ansys.pyoptics.speos'],
    version=__version__,
    description='PyOptics library',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/pyansys/pyoptics',
    license='MIT',
    author='ANSYS, Inc.',
    author_email='pyansys.support@ansys.com',
    maintainer='PyAnsys developers',
    maintainer_email='pyansys.support@ansys.com',
    install_requires=[
        'ansys-optics-grpcapi>=2',
        'grpcio-tools'
    ],
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
