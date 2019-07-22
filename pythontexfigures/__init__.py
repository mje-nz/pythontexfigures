import functools

from .pythontexfigures import *

_setup = setup
def setup(*args, **kwargs):
    _setup(*args, **kwargs)
    # Re-import constants now that they're set
    globals().update((k, v) for (k, v) in _setup.__globals__.items()
                     if k in globals() and globals()[k] is None)
functools.update_wrapper(setup, _setup)
