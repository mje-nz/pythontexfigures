"""Tests for implementation details of the LaTeX package."""
from pathlib import Path

import pytest

from util import build  # noqa: I900

DOCUMENT_TEMPLATE = r"""
\documentclass{article}
\usepackage{pgf}
\usepackage[keeptemps=all]{pythontex}
\usepackage{pythontexfigures}

\begin{document}
\pyfig[%(options)s]{%(name)s}[%(args)s]
\end{document}
"""

SCRIPT = """
def main(*args, **kwargs):
    open("args.txt", "w").write(f"{repr(args)}, {repr(kwargs)}")
"""


def document(args="", name="test.py", options=""):
    """Fill in LaTeX document template."""
    return DOCUMENT_TEMPLATE % dict(args=args, name=name, options=options)


@pytest.mark.parametrize(
    "args,expected",
    (
        ("'test'", "('test',), {}"),
        ('"test"', "('test',), {}"),
        ("{{'a': 1}}", "({'a': 1},), {}"),
        ("{'a': 1},test=True", "({'a': 1},), {'test': True}"),
        ("{'a': 1}, test=True", "({'a': 1},), {'test': True}"),
        ("{{'a': 1},test=True}", "({'a': 1},), {'test': True}"),
        ("(1, 2, 3)", "((1, 2, 3),), {}"),
    ),
)
def test_sanitizing_arguments(in_temp_dir, args, expected):
    """Test sanitizing figure script arguments."""
    Path("main.tex").write_text(document(args))
    Path("test.py").write_text(SCRIPT)
    build("main.tex")
    assert Path("args.txt").read_text() == expected


@pytest.mark.parametrize("name", ("'test.py'", '"test.py"'))
def test_quoted_filename(in_temp_dir, name):
    """Test quoted figure script filenames work."""
    Path("main.tex").write_text(document(name=name))
    Path("test.py").write_text(SCRIPT)
    build("main.tex")
    assert Path("args.txt").read_text() == "(), {}"
