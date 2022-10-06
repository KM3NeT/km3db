#!/usr/bin/env python3


def pandas():
    """Imports and returns ``pandas``."""
    try:
        import pandas
    except ImportError:
        raise ImportError(
            "install the 'pandas' package with:\n\n"
            "    pip install pandas\n\n"
            "or\n\n"
            "    conda install pandas"
        )
    else:
        return pandas


def h5py():
    """Imports and returns ``h5py``."""
    try:
        import h5py
    except ImportError:
        raise ImportError(
            "install the 'h5py' package with:\n\n"
            "    pip install h5py\n\n"
            "or\n\n"
            "    conda install h5py"
        )
    else:
        return h5py
