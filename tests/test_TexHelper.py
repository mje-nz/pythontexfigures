r"""Tests for handling \pyfig arguments."""


from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from pythontexfigures.pythontexfigures import TexHelper, _calculate_figure_name


def fake_pytex(fontsize="10", textwidth="5", linewidth="2", **context):
    """Construct a mock PythonTeXUtils object with the given attribute in context."""
    pytex = Mock()
    pytex.context = SimpleNamespace(
        fontsize=fontsize, textwidth=textwidth, linewidth=linewidth, **context
    )
    pytex.pt_to_in = lambda x: float(x)
    return pytex


def test_construct():
    """Test constructing a TexHelper with a fake PythonTeXUtils instance."""
    helper = TexHelper(fake_pytex())
    assert helper


def test_parse_args_empty():
    """Test parsing an empty argument string."""
    helper = TexHelper(fake_pytex())
    args, kwargs = helper._parse_pyfig_args("")
    assert args == ()
    assert kwargs == {}


@pytest.mark.parametrize(
    "width,expected",
    (
        ("1", 1),
        (r"0.5\textwidth", 2.5),
        (r"0.5\textwidth{}", 2.5),
        (r"0.5\textwidth {}", 2.5),
        (r"0.75\linewidth", 1.5),
        (r"0.75\linewidth{}", 1.5),
    ),
)
def test_parse_width(width, expected):
    """Test parsing width arguments."""
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args(f"width={width}")
    assert kwargs == dict(width=expected)


@pytest.mark.parametrize("options,expected", (("aspect=1.5", 1.5), ("golden", 1.618)))
def test_parse_aspect(options, expected):
    """Test parsing aspect ratio arguments."""
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args(options)
    assert kwargs == pytest.approx(dict(aspect=expected), abs=0.001)


def test_parse_unexpected():
    """Test parsing a mixture of unknown positional and keyword arguments"""
    helper = TexHelper(fake_pytex())
    args, kwargs = helper._parse_pyfig_args("1, unknown1='a'")
    assert args == (1,)
    assert kwargs == dict(unknown1="a")


def test_parse_tuple():
    """Test parsing a tuple literal."""
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args("x=(1, 2, 3), next=4")
    assert kwargs == dict(x=(1, 2, 3), next=4)


def test_parse_dict():
    """Test parsing a dict literal."""
    helper = TexHelper(fake_pytex())
    # Braces have to be escaped, but the backslash still come through
    args, _ = helper._parse_pyfig_args(r"\{'a': 1\}")
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
