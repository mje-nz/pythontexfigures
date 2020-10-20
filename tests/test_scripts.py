"""Integration tests for installer and sty helper.

Author: Matthew Edwards
Date: July 2019
"""

import subprocess


def test_install():
    """Just check pythontexfigures.install exists."""
    import pythontexfigures.install  # noqa: F401

    # TODO More thorough


def test_sty():
    """Check pythontexfigures.sty prints the LaTeX package."""
    output = subprocess.check_output("python3 -m pythontexfigures.sty".split(" "))
    expected = open("pythontexfigures/pythontexfigures.sty", "rb").read()
    assert output.strip() == expected.strip()
