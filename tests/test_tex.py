r"""Tests for handling \pyfig arguments."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pythontexfigures.tex import (
    FigureContext,
    TexHelper,
    _calculate_figure_name,
    evaluate_arg_str,
    with_context,
)


def fake_pytex(fontsize="10", textwidth="5", linewidth="2", **context):
    """Construct a mock PythonTeXUtils object with the given attribute in context."""
    pytex = Mock()
    pytex.context = SimpleNamespace(
        fontsize=fontsize,
        textwidth=textwidth,
        linewidth=linewidth,
        scriptpath=".",
        currdir=".",
        outputdir=".",
        **context,
    )
    pytex.open = open
    pytex.pt_to_in = lambda x: float(x)
    return pytex


def test_construct():
    """Test constructing a TexHelper with a fake PythonTeXUtils instance."""
    helper = TexHelper(fake_pytex())
    assert helper


def test_parse_options_empty():
    """Test parsing an empty options string."""
    helper = TexHelper(fake_pytex())
    width, height, kwargs = helper._parse_pyfig_options("")
    # Default is linewidth x linewidth
    assert width == 2
    assert height == 2
    assert kwargs == {}


@pytest.mark.parametrize(
    "width,expected",
    (
        ("1", 1),
        ("1pt", 1),
        ("1in", 72.27),
        ("1cm", 72.27 / 2.54),
        ("1mm", 72.27 / 25.4),
        (r"0.5\textwidth", 2.5),
        (r"0.5\textwidth{}", 2.5),
        (r"0.5\textwidth {}", 2.5),
        (r"0.75\linewidth", 1.5),
        (r"0.75\linewidth{}", 1.5),
    ),
)
def test_parse_width(width, expected):
    """Test parsing width option."""
    helper = TexHelper(fake_pytex())
    width, _, _ = helper._parse_pyfig_options(f"width={width}")
    assert width == expected


@pytest.mark.parametrize(
    "options,expected", (("1,aspect=1.5", 1.5), ("1,golden", 1.618))
)
def test_parse_aspect(options, expected):
    """Test parsing aspect ratio option."""
    helper = TexHelper(fake_pytex())
    width, height, _ = helper._parse_pyfig_options(options)
    assert width == 1
    assert height == pytest.approx(width / expected, abs=0.001)


def test_parse_unexpected():
    """Test parsing a mixture of unknown positional and keyword arguments"""
    args, kwargs = evaluate_arg_str("1, unknown1='a'")
    assert args == (1,)
    assert kwargs == dict(unknown1="a")


def test_parse_tuple():
    """Test parsing a tuple literal."""
    _, kwargs = evaluate_arg_str("x=(1, 2, 3), next=4")
    assert kwargs == dict(x=(1, 2, 3), next=4)


def test_parse_dict():
    """Test parsing a dict literal."""
    # N.B. This needs extra braces when entered in TeX, but they don't come through
    args, _ = evaluate_arg_str("{'a': 1}")
    assert args == ({"a": 1},)


@pytest.mark.parametrize(
    "name,args,kwargs,expected",
    (
        ("fig", (), {}, "fig"),
        ("fig", (1,), {"temp": True}, "fig-1-temp-True"),
        ("fig", ([1, 2, 3],), {}, "fig-1,2,3"),
        ("fig", ((1, 2, 3),), {}, "fig-1,2,3"),
        ("fig", ({"a": 1, "b": 2},), {}, "fig-a1,b2"),
        ("fig", ("test",), {}, "fig-test"),
        ("fig", ("\n",), {}, "fig"),
        ("fig", ("test\n",), {}, "fig-test"),
    ),
)
def test_default_name(name, args, kwargs, expected):
    """Test coming up with sensible default names for figure output files."""
    actual = _calculate_figure_name(name, args, kwargs)
    assert actual == expected


SCRIPT = """
def main(*args, **kwargs):
    open("args.txt", "w").write(f"{repr(args)}, {repr(kwargs)}")
"""


@pytest.mark.parametrize("options,args", (("", ""), ("", "'test'"), ("width=1", "")))
def test_draw(in_temp_dir, options, args):
    """Test a simple figure drawing scenario without all the LaTeX."""
    Path("test.py").write_text(SCRIPT)
    helper = TexHelper(fake_pytex())
    helper.figure(".test.py.", f".{options}.", f".{args}.")


class DrawCalled(Exception):
    """Dummy exception for interrupting drawing."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@with_context
def draw_with_context(ctx, arg):
    """Dummy figure function which expects a context."""
    assert ctx is not None
    assert arg is not None
    raise DrawCalled()


def test_context():
    """Test passing context object to figure functions."""
    ctx = FigureContext(None, "test", 1, 1, figure_func=draw_with_context)
    with pytest.raises(DrawCalled):
        ctx.draw(1)
