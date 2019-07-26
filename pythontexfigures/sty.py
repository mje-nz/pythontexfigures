"""Wrapper for reading pythontexfigures.sty from wherever it gets packaged.

Author: Matthew Edwards
Date: July 2019
"""

from pathlib import Path


def sty_file_as_string():
    """Get the contents of pythontexfigures.sty as string."""
    # importlib.resources.read_text would be better, but I don't feel like adding
    # a dependency.  pkg_resources does a bunch of weird stuff.  Instead, I've just
    # set zip_safe=False so this is always a real file.
    return (Path(__file__).parent / "pythontexfigures.sty").open().read()


if __name__ == "__main__":
    print(sty_file_as_string())
