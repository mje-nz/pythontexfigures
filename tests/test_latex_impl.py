"""Tests for implementation details of the LaTeX package."""
from pathlib import Path

import pytest

from .util import build

DOCUMENT_TEMPLATE = r"""
\documentclass{article}
\usepackage{pgf}
\usepackage{pythontex}
\usepackage{pythontexfigures}

\begin{document}
\pyfig[%(args)s]{test.py}
\end{document}
"""

SCRIPT = """
def main(*args, **kwargs):
    open("args.txt", "w").write(f"{repr(args)}, {repr(kwargs)}")
"""


def document(args):
    """Fill in LaTeX document template."""
    return DOCUMENT_TEMPLATE % dict(args=args)


@pytest.mark.parametrize(
    "args,expected",
    (
        ("'test'", "('test',), {}"),
        ('"test"', "('test',), {}"),
        (r"\{'a': 1\}", "({'a': 1},), {}"),
        ("(1, 2, 3)", "((1, 2, 3),), {}"),
    ),
)
def test_sanitizing_arguments(in_temp_dir, args, expected):
    """Test sanitizing figure script arguments."""
    Path("main.tex").write_text(document(args))
    Path("test.py").write_text(SCRIPT)
    build("main.tex")
    assert Path("args.txt").read_text() == expected
