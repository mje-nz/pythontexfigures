"""Tests for pythontexfigures package options."""
import os
import subprocess
from pathlib import Path

import pytest

DOCUMENT_TEMPLATE = r"""
\documentclass{article}
%(pre)s
\usepackage{pgf}
\usepackage{pythontex}
\usepackage[%(options)s]{pythontexfigures}
%(post)s

\begin{document}
%(body)s
\end{document}
"""

BODY = r"\pyfig{test.py}"

SCRIPT = """
import matplotlib

def main():
    open("result.txt", "w").write(str(matplotlib.rcParams["font.size"]))
"""


def document(options="", pre="", post="", body=BODY):
    """Fill in LaTeX document template."""
    return DOCUMENT_TEMPLATE % dict(options=options, pre=pre, post=post, body=body)


@pytest.fixture
def in_temp_dir(tmp_path):
    """Changes working directory and returns to previous on exit."""
    # https://stackoverflow.com/a/42441759
    prev_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def build(filename: str):
    """Use pdflatex and pythontex to build the given tex document."""
    pdflatex = ["pdflatex", "-interaction=nonstopmode", filename]
    pythontex = ["pythontex", filename]

    result = subprocess.run(pdflatex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "First pdflatex run failed: " + result.stdout
    result = subprocess.run(pythontex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "pythontex failed: " + result.stdout
    result = subprocess.run(pdflatex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "Second pdflatex run failed: " + result.stdout


def test_build_default(in_temp_dir):
    """Test building a simple document with a simple figure using default options."""
    Path("main.tex").write_text(document())
    Path("test.py").write_text(SCRIPT)
    build("main.tex")


def test_missing_figure(in_temp_dir):
    """Test build fails if a figure script is missing."""
    Path("main.tex").write_text(document())
    with pytest.raises(AssertionError):
        build("main.tex")


def test_build_in_subfolder(in_temp_dir):
    """Test keeping scripts in a subfolder."""
    Path("main.tex").write_text(document(post=r"\pythontexfigurespath{scripts}"))
    Path("scripts").mkdir()
    Path("scripts/test.py").write_text(SCRIPT)
    build("main.tex")


@pytest.mark.parametrize(
    "name,expected",
    (
        ("normalsize", 10),
        ("small", 9),
        ("footnotesize", 8),
        ("scriptsize", 7),
        ("6", 6),
    ),
)
def test_font_size(in_temp_dir, name: str, expected: float):
    """Test building with different font sizes."""
    Path("main.tex").write_text(document(options="fontsize=" + name))
    Path("test.py").write_text(SCRIPT)
    build("main.tex")
    assert float(Path("result.txt").read_text()) == expected


def test_relative(in_temp_dir):
    """Test building with the relative option."""
    Path("main.tex").write_text(
        document(
            options="relative",
            pre=r"\usepackage[abspath]{currfile}",
            body=r"\include{tex/body.tex}",
        )
    )
    Path("tex").mkdir()
    Path("tex/body.tex").write_text(BODY)
    Path("tex/test.py").write_text(SCRIPT)
    build("main.tex")


def test_relative_subfolder(in_temp_dir):
    """Test building with the relative option and scripts in a subfolder."""
    Path("main.tex").write_text(
        document(
            options="relative",
            pre=r"\usepackage[abspath]{currfile}",
            post=r"\pythontexfigurespath{scripts}",
            body=r"\include{tex/body.tex}",
        )
    )
    Path("tex/scripts").mkdir(parents=True)
    Path("tex/body.tex").write_text(BODY)
    Path("tex/scripts/test.py").write_text(SCRIPT)
    build("main.tex")
