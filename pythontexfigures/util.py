"""Utility functions.

Author: Matthew Edwards
Date: July 2019
"""
import os  # noqa: F401
from typing import List, Union

# From typeshed
StrPath = Union[str, "os.PathLike[str]"]


def section_of_file(filename: StrPath, from_expr, to_expr) -> List[str]:
    """Get the section of a file between the lines matching two expressions.

    Args:
        filename: File to read.
        from_expr (Callable[[str], bool]): Function to match the starting line.
        to_expr (Callable[[str], bool]): Function to match the ending line.

    Returns:
        The lines in between the lines matched by from_expr and to_expr.
    """
    output = []
    with open(filename) as f:
        for line in f:
            if from_expr(line):
                # Found start
                break
        else:
            # Never found start
            raise ValueError("Start expression unmatched")
        for line in f:
            if to_expr(line):
                # Found end
                break
            else:
                output.append(line)
        else:
            # Never found end
            raise ValueError("End expression unmatched")
    return output
