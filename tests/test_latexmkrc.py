"""Unit tests for latexmkrc module.

Author: Matthew Edwards
Date: July 2019
"""

import textwrap
from pathlib import Path

import pytest

from pythontexfigures import latexmkrc


@pytest.fixture
def out_dir(tmpdir):
    """Construct some fake PythonTeX .out files."""
    (Path(tmpdir) / "py_basic_default.out").open("w").write(
        textwrap.dedent(
            r"""
            =>PYTHONTEX:STDOUT#0CC#code#
            =>PYTHONTEX:STDOUT#0#i#
            \input{pythontex-files-example/test-5.40x5.40.pgf}
            =>PYTHONTEX:STDOUT#1#i#
            \input{pythontex-files-example/test-2.43x1.50.pgf}
            =>PYTHONTEX:STDOUT#2#i#
            \input{pythontex-files-example/test-2.43x2.43.pgf}
            =>PYTHONTEX:DEPENDENCIES#
            /Users/Matthew/Code/Uni/latex-python-figures/pythontexfigures/pythontexfigures.py
            scripts/test.py
            scripts/test.py
            scripts/test.py
            =>PYTHONTEX:CREATED#
            pythontex-files-example/test-5.40x5.40.pgf
            pythontex-files-example/test-2.43x1.50.pgf
            pythontex-files-example/test-2.43x2.43.pgf
            """
        )
    )
    (Path(tmpdir) / "py_subfiles_default.out").open("w").write(
        textwrap.dedent(
            r"""
            =>PYTHONTEX:STDOUT#0CC#code#
            =>PYTHONTEX:STDOUT#0#i#
            \input{pythontex-files-example-with-subfiles/poynomial-2-0-0-5.40x5.40.pgf}
            =>PYTHONTEX:STDOUT#1#i#
            \input{pythontex-files-example-with-subfiles/poynomial-2-0-0-0-5.40x5.40.pgf}
            =>PYTHONTEX:DEPENDENCIES#
            /Users/Matthew/Code/Uni/latex-python-figures/pythontexfigures/pythontexfigures.py
            scripts/polynomial.py
            scripts/polynomial.py
            =>PYTHONTEX:CREATED#
            pythontex-files-example-with-subfiles/poynomial-2-0-0-5.40x5.40.pgf
            pythontex-files-example-with-subfiles/poynomial-2-0-0-0-5.40x5.40.pgf
            """
        )
    )
    return tmpdir


def test_dependecy_rules_for_file(out_dir):
    deps = latexmkrc.dependencies_in_out_file(Path(out_dir) / "py_basic_default.out")
    assert sorted(set(deps)) == [
        "/Users/Matthew/Code/Uni/latex-python-figures/pythontexfigures/pythontexfigures.py",
        "scripts/test.py",
    ]

    deps2 = latexmkrc.dependencies_in_out_file(
        Path(out_dir) / "py_subfiles_default.out"
    )
    assert sorted(set(deps2)) == [
        "/Users/Matthew/Code/Uni/latex-python-figures/pythontexfigures/pythontexfigures.py",
        "scripts/polynomial.py",
    ]


def test_dependency_rules_for_folder(out_dir):
    rules = latexmkrc.dependency_rules_for_folder(out_dir)
    assert sorted(rules) == [
        "rdb_ensure_file($rule, '/Users/Matthew/Code/Uni/latex-python-figures/pythontexfigures/pythontexfigures.py');",
        "rdb_ensure_file($rule, 'scripts/polynomial.py');",
        "rdb_ensure_file($rule, 'scripts/test.py');",
    ]


@pytest.fixture
def out_dir_without_deps(tmpdir):
    """Construct some fake PythonTeX .out files with no dependencies."""
    (Path(tmpdir) / "py_basic_default.out").open("w").write(
        textwrap.dedent(
            r"""
            =>PYTHONTEX:STDOUT#0CC#code#
            =>PYTHONTEX:STDOUT#0#i#
            \input{pythontex-files-example/test-5.40x5.40.pgf}
            =>PYTHONTEX:DEPENDENCIES#
            """
        )
    )
    (Path(tmpdir) / "py_subfiles_default.out").open("w").write(
        textwrap.dedent(
            r"""
            =>PYTHONTEX:STDOUT#0CC#code#
            =>PYTHONTEX:STDOUT#0#i#
            \input{pythontex-files-example-with-subfiles/poynomial-2-0-0-5.40x5.40.pgf}
            """
        )
    )
    return tmpdir


def test_dependecy_rules_for_folder_without_deps(out_dir_without_deps):
    assert latexmkrc.dependency_rules_for_folder(out_dir_without_deps) == []


def test_dependecy_rules_for_empty_folder(tmpdir):
    assert latexmkrc.dependency_rules_for_folder(tmpdir) == []
