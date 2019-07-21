"""Wrapper for reading pythontexfigures.sty from wherever it gets packaged.

Author: Matthew Edwards
Date: July 2019
"""

import pkg_resources


def sty_file_as_string():
    sty = pkg_resources.resource_string(__name__, "pythontexfigures.sty")  # type: bytes
    return sty.decode('utf8')


if __name__ == '__main__':
    print(sty_file_as_string())
