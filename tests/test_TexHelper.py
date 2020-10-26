r"""Tests for handling \pyfig arguments."""


from pythontexfigures import TexHelper
from types import SimpleNamespace
from unittest.mock import Mock
import pytest


def fake_pytex(fontsize="10", textwidth="5", linewidth="2", **context):
    pytex = Mock()
    pytex.context = SimpleNamespace(
        fontsize=fontsize, textwidth=textwidth, linewidth=linewidth, **context
    )
    pytex.pt_to_in = lambda x: float(x)
    return pytex


def test_construct():
    helper = TexHelper(fake_pytex())
    assert helper


def test_parse_args_basic():
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
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args(f"width={width}")
    assert kwargs == dict(width=expected)


@pytest.mark.parametrize("options,expected", (("aspect=1.5", 1.5), ("golden", 1.618)))
def test_parse_aspect(options, expected):
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args(options)
    assert kwargs == pytest.approx(dict(aspect=expected), abs=0.001)


def test_parse_unexpected():
    helper = TexHelper(fake_pytex())
    args, kwargs = helper._parse_pyfig_args("1, unknown1='a'")
    assert args == (1,)
    assert kwargs == dict(unknown1="a")


def test_parse_tuple():
    helper = TexHelper(fake_pytex())
    _, kwargs = helper._parse_pyfig_args("x=(1, 2, 3), next=4")
    assert kwargs == dict(x=(1, 2, 3), next=4)
