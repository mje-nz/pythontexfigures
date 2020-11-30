"""Drawing routines, which don't interact with PythonTeX at all."""
import re
from pathlib import Path
from typing import Callable, Optional

import matplotlib as mpl
import seaborn as sns

from .util import StrPath

# When generating PDF figures, use PGF backend so it looks the same as it will when
# called from LaTeX
mpl.use("pgf")
import matplotlib.pyplot as plt  # noqa: E402 isort:skip


def setup_matplotlib(font_size: float = None):
    """Set up matplotlib.

    Args:
        font_size: Override base font size (in pt), defaults to document's font
            size (or matplotlib default in standalone mode).
    """
    # Base style
    sns.set_style("white")
    sns.set_palette("muted", color_codes=True)

    # Set up PGF backend
    mpl.rcParams.update(
        {
            # Use pdflatex instead of xelatex
            "pgf.texsystem": "pdflatex",
            # Use LaTeX instead of mathtext for all text rendering
            "text.usetex": True,
            # Fix input and font encoding
            "pgf.preamble": "\n".join(
                [r"\usepackage[utf8x]{inputenc}", r"\usepackage[T1]{fontenc}"]
            ),
        }
    )

    # Use default LaTeX fonts (to match appearance for PDFs, to get correct layout for
    # PGFs)
    mpl.rcParams.update({"font.family": "serif", "pgf.rcfonts": False})

    # Set base font size
    if font_size:
        mpl.rcParams["font.size"] = font_size

    mpl.rcParams.update(
        {
            # Make axes border line width slightly thinner
            "axes.linewidth": 0.6,
            # Reduce legend label spacing slightly
            "legend.labelspacing": "0.3",
            # Set default figure DPI to appropriate value for print
            "figure.dpi": 300,
        }
    )


def _figure_tweaks():
    """Adjust figure before saving."""
    # From https://github.com/bcbnz/matplotlib-pgfutils/blob/ddd71596659718a8b55ca511a112df5ea1b5d7a8/pgfutils.py#L706  # noqa: B950
    for axes in plt.gcf().get_axes():
        # There is no rcParam for the legend border line width, so manually adjust it
        # to match the default axes border line width
        legend = axes.get_legend()
        if legend:
            frame = legend.get_frame()
            frame.set_linewidth(mpl.rcParams["axes.linewidth"])


def _pgf_tweaks(filename: StrPath):
    """Adjust PGF file after saving."""
    file = Path(filename)
    pgf_text = file.read_text()

    # Not sure precisely what the behaviour is, but sometimes axis labels get stuck sans
    # or sans-serif regardless of font.family.  Let's just remove all the font family
    # selection and match the document font.
    # TODO: Figure out exactly what causes this and report bug
    pgf_text = pgf_text.replace(r"\rmfamily", "")
    pgf_text = pgf_text.replace(r"\sffamily", "")

    # Regex which matches image commands, splitting the filename by extension
    pattern = re.compile(
        r"(\\(?:pgfimage|includegraphics)(?:\[.+?\])?{)([^}]+)(\..+?})"
    )

    # From https://github.com/bcbnz/matplotlib-pgfutils/blob/de2b3651cf359da2263864238f81ed3a4a860d4a/pgfutils.py#L793  # noqa: B950
    if file.parent.absolute() != Path(".").absolute():
        # If the PGF file is not in the top-level directory (which it isn't by default),
        # fix the paths in \pgfimage and \includegraphics commands (for rasterised
        # plots).  I think matplotlib might have changed from one to the other at some
        # points.
        prefix = str(file.parent.relative_to("."))
        replacement = r"\1{0:s}/\2\3".format(prefix)
        pgf_text = re.sub(pattern, replacement, pgf_text)

    # Escape dots in image filenames
    pgf_text = re.sub(pattern, r"\1{\2}\3", pgf_text)

    file.write_text(pgf_text)


def draw_figure(
    figure_func: Callable,
    name: str,
    width: float,
    height: float,
    output_dir: Optional[StrPath] = None,
    format_: str = "pgf",
    verbose: bool = False,
):
    """Draw a figure, using a callback for the actual drawing.

    This function sets up a matplotlib figure, calls a function to draw in it, then
    saves it in the given location and format and returns the filename.

    Args:
        figure_func: A function which takes no arguments and draws a figure.
        name: The stem for the figure filename.
        width: The figure width in inches.
        height: The figure height in inches.
        aspect: The figure aspect ratio (width/height), which is used to
            calculate the height if unspecified (default 1).
        output_dir: The directory in which to save the figure.
        format_: The file format in which to save the figure ('pdf' or 'pgf').
        verbose: Whether to print log messages to stdout.

    Returns:
        The saved figure's full path.
    """
    # TODO: tests for figure size
    figure_size = (width, height)
    plt.figure(figsize=figure_size)

    # Run figure function, then reset mpl.rcParams
    if verbose:
        print("Drawing...")
    with mpl.rc_context():
        figure_func()

    # Generate name for figure
    assert name is not None
    name += "-%.2fx%.2f" % figure_size

    # Save figure
    if verbose:
        print("Saving...")
    _figure_tweaks()
    if output_dir is None:
        output_dir = "."
    assert Path(output_dir).is_dir(), "Output dir does not exist"
    figure_filename = Path(output_dir) / (name + "." + format_)
    # TODO: Check if already created this run
    plt.savefig(figure_filename, bbox_inches="tight", pad_inches=0)
    plt.close("all")

    if format_ == "pgf":
        _pgf_tweaks(figure_filename)

    return figure_filename
