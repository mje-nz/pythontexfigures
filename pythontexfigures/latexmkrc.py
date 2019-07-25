"""Helpers for adding PythonTeX support to latexmkrc.

Author: Matthew Edwards
Date: July 2019
"""

import glob
import sys
from pathlib import Path

from .util import section_of_file


def latexmkrc_as_string():
    """Return the content of `latexmkrc` as a string."""
    # importlib.resources.read_text would be better, but I don't feel like adding
    # a dependency.  pkg_resources does a bunch of weird stuff.  Instead, I've just
    # set zip_safe=False so this is always a real file.
    return (Path(__file__).parent / "latexmkrc").open().read()


def dependencies_in_out_file(filename):
    """Extract the dependency list from a PythonTeX .out file.

    Args:
        filename (str): A PythonTeX .out file.

    Returns:
        list[str]: The dependencies as a list of filenames.
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


def dependency_rules_for_folder(folder):
    """Return latexmk dependency rules for all the PythonTeX dependencies in a
    PythonTeX output directory.

    Args:
        folder (str): A PythonTeX output directory.

    Returns:
        list[str]: Perl commands to add each dependency.
    """
    deps = []
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
