#!/usr/bin/env python
# Filename: setup.py
"""
The km3db setup script.

"""
from setuptools import setup
import sys


def read_stripped_lines(filename):
    """Return a list of stripped lines from a file"""
    with open(filename) as fobj:
        return [l.strip() for l in fobj.readlines()]


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
    python_requires=">=3.5",
    install_requires=read_stripped_lines("requirements.txt"),
    extras_require={"dev": read_stripped_lines("requirements-dev.txt")},
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python",
    ],
)
