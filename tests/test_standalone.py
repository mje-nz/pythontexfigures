"""Tests for running figure scripts using run_standalone."""
import matplotlib.pyplot as plt

from pythontexfigures import run_standalone


def simple_plot():
    """Plot a straight line."""
    plt.plot([0, 1], [0, 1])


def test_standalone(in_temp_dir):
    """Test that run_standlone doesn't crash."""
    run_standalone(simple_plot)
