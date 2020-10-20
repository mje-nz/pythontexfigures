"""pythontexfigures package."""

from .pythontexfigures import TexHelper, run_standalone
from .sty import print_preamble


def setup(*args, **kwargs):
    return TexHelper(*args, **kwargs)
