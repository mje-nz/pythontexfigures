"""Unit tests for utility functions.

Author: Matthew Edwards
Date: July 2019
"""

import string
from pathlib import Path

import pytest

from pythontexfigures import util


@pytest.fixture
def alphabet_file(tmpdir):
    """Fill a temporary file with the alphabet, one letter per line."""
    filename = Path(tmpdir) / "data"
    open(filename, "w").write("\n".join(string.ascii_lowercase))
    return filename


def test_section_of_file(alphabet_file):
    """Test util.section_of_file succeeding."""
    hijklmnop = util.section_of_file(
        alphabet_file, lambda line: line == "g\n", lambda line: line == "q\n"
    )

    assert hijklmnop == [letter + "\n" for letter in "hijklmnop"]


def test_section_of_file_no_start(alphabet_file):
    """Test util.section_of_file missing the start."""
    with pytest.raises(ValueError):
        util.section_of_file(
            alphabet_file, lambda line: line == "missing\n", lambda line: line == "z\n"
        )


def test_section_of_file_no_end(alphabet_file):
    """Test util.section_of_file missing the end."""
    with pytest.raises(ValueError):
        util.section_of_file(
            alphabet_file, lambda line: line == "a\n", lambda line: line == "missing\n"
        )
