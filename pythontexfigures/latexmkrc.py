"""Helpers for adding PythonTeX support to latexmkrc.

Author: Matthew Edwards
Date: July 2019
"""

import glob
import sys
from pathlib import Path
from typing import List

from .util import StrPath, section_of_file


def latexmkrc_as_string():
    """Return the content of `latexmkrc` as a string."""
    # importlib.resources.read_text would be better, but I don't feel like adding
    # a dependency.  pkg_resources does a bunch of weird stuff.  Instead, I've just
    # set zip_safe=False so this is always a real file.
    return (Path(__file__).parent / "latexmkrc").open().read()


def dependencies_in_out_file(filename: StrPath) -> List[str]:
    """Extract the dependency list from a PythonTeX .out file.

    Args:
        filename: A PythonTeX .out file.

    Returns:
        The dependencies as a list of filenames.
    """
    try:
        deps = section_of_file(
            filename,
            lambda line: line == "=>PYTHONTEX:DEPENDENCIES#\n",
            lambda line: line.startswith("=>"),
        )
        return [line.strip() for line in deps]
    except ValueError:
        return []


def dependency_rules_for_folder(folder: StrPath) -> List[str]:
    """Construct latexmk rules for all the PythonTeX dependencies in a folder.

    Args:
        folder: A PythonTeX directory containing py_*.out files to get
            dependencies from.

    Returns:
        Perl commands for latexmkrc which add each dependency.
    """
    deps: List[str] = []
    for filename in glob.glob(str(Path(folder) / "*.out")):
        deps += dependencies_in_out_file(filename)
    rules = [f"rdb_ensure_file($rule, '{filename}');" for filename in set(deps)]
    return rules


if __name__ == "__main__":
    # TODO: Not lazy
    if "--get-deps" in sys.argv:
        assert len(sys.argv) == 3
        print("\n".join(dependency_rules_for_folder(sys.argv[2])))
    else:
        print(latexmkrc_as_string())
