#!/usr/bin/env python
# Filename: setup.py
"""
The km3db setup script.

"""
from setuptools import setup
import os
import sys


def read_requirements(kind):
    """Return a list of stripped lines from a file"""
    with open(os.path.join("requirements", kind + ".txt")) as fobj:
        requirements = [l.strip() for l in fobj.readlines()]
    v = sys.version_info
    if (v.major, v.minor) < (3, 6):
        try:
            requirements.pop(requirements.index("black"))
        except ValueError:
            pass
    return requirements


try:
    with open("README.rst") as fh:
        long_description = fh.read()
except UnicodeDecodeError:
    long_description = "KM3NeT database library"

setup(
    name="km3db",
    url="https://git.km3net.de/km3py/km3db",
    description="KM3NeT database library",
    long_description=long_description,
    author="Tamas Gal",
    author_email="tgal@km3net.de",
    packages=["km3db"],
    include_package_data=True,
    platforms="any",
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    python_requires=">=2.7",
    install_requires=read_requirements("install"),
    extras_require={kind: read_requirements(kind) for kind in ["dev", "extras"]},
    entry_points={
        "console_scripts": [
            "km3db=km3db.cli.km3db:main",
            "streamds=km3db.cli.streamds:main",
            "detx=km3db.cli.detx:main",
            "runtable=km3db.cli.runtable:main",
            "runinfo=km3db.cli.runinfo:main",
            "wtd=km3db.cli.wtd:main",
        ],
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
    ],
)
