"""PythonTeX figure helpers.

Author: Matthew Edwards
Date: July 2019
"""
import glob
import inspect
import math
import re
import textwrap
from pathlib import Path
from typing import Callable, Optional  # noqa: F401

import matplotlib as mpl

# When generating PDF figures, use PGF backend so it looks the same as it will when
# called from LaTeX
mpl.use("pgf")
import matplotlib.pyplot as plt  # noqa: E402 isort:skip

from .util import section_of_file  # noqa: E402 isort:skip


def setup_matplotlib(font_size=None):
    """Set up matplotlib.

    Args:
        font_size (float): Override base font size (in pt), defaults to document's font
            size (or matplotlib default in standalone mode).
    """
    # Set up PGF backend
    mpl.rcParams.update(
        {
            # Use pdflatex instead of xelatex
            "pgf.texsystem": "pdflatex",
            # Use LaTeX instead of mathtext for all text rendering
            "text.usetex": True,
            # Fix input and font encoding
            "pgf.preamble": "\n".join([
                r"\usepackage[utf8x]{inputenc}",
                r"\usepackage[T1]{fontenc}",
            ]),
        }
    )

    # Use default LaTeX fonts (to match appearance for PDFs, to get correct layout for
    # PGFs)
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "pgf.rcfonts": False,
        }
    )

    # Set base font size
    if font_size:
        mpl.rcParams["font.size"] = font_size

    mpl.rcParams.update(
        {
            # Make axes border line width slightly thinner
            "axes.linewidth": 0.6,
            # Reduce legend label spacing slightly
            "legend.labelspacing": "0.3",
        }
    )


class TexHelper:

    r"""Implementation for \pyfig command."""

    SQUARE = 1
    GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0

    def __init__(self, pytex):
        """Configure matplotlib and save pytex context.

        Call this at the start of the PythonTeX custom code, **before** importing
        matplotlib.

        Args:
            pytex (pythontex_utils.PythonTeXUtils): The global PythonTeXUtils instance.
        """
        assert pytex is not None
        self.pytex = pytex

        setup_matplotlib(self.font_size)

        # Re-run pythontex when files in this package change
        for path in sorted(Path(__file__).parent.iterdir()):
            if path.is_file():
                pytex.add_dependencies(path)

    @property
    def font_size(self):
        """The font size from the PythonTeX context, in points."""
        # The value in the context is either a size in points, or whatever the user
        # specified
        return float(self.pytex.context.fontsize.strip(" pt"))

    @property
    def text_width(self):
        """The font size from the PythonTeX context, in inches."""
        return self.pytex.pt_to_in(self.pytex.context.textwidth)

    @property
    def output_dir(self):
        """The directory in which to save figures, from the PythonTeX context."""
        return Path(self.pytex.context.outputdir)

    @property
    def script_path(self):
        """The folder to search for figure scripts."""
        # Value of the "scriptpath" package option
        script_path_option = self.pytex.context.scriptpath
        # If the "relative" package option is set, this is the absolute path of the
        # dir containing the current TeX file, and script_path is relative to it.
        current_file_dir = self.pytex.context.currdir

        # By default,  look for scripts relative to the current working directory
        root = Path()

        if current_file_dir:
            # With the "relative" package option, look for scripts relative to the file
            # being processed
            root = Path(current_file_dir)
            if script_path_option:
                # Sanity check
                assert not Path(script_path_option).is_absolute()
        return root / script_path_option

    def _find_script(self, script_name: str):
        """Find a figure script by name.

        The path from pythontexfigures is used.  With package option 'relative', the
        path is relative to the file being processed.

        Args:
            script_name (str): The filename of the script, either as an absolute path or
                relative to the script search path.

        Returns:
            Path: Script path.
        """
        script_name = Path(script_name)
        if script_name.is_absolute():
            # TODO: This seems like it misses the non-relative case
            assert script_name.exists()
            return script_name

        script_path = self.script_path / script_name
        assert script_path.exists(), f"Script {script_path} not found ({script_path.resolve()})"
        return script_path

    def _load_script(self, script_name):
        """Load the main() function from the given script.

        Args:
            script_name (str): The filename of the script, either as an absolute path or
                relative to the script search path.

        Returns:
            Callable[..., str]: The main() function.
        """
        script_path = self._find_script(script_name)

        globals_ = dict(__file__=str(script_path), __name__=script_path.stem)
        # https://stackoverflow.com/a/41658338
        with self.pytex.open(script_path, "rb") as file:
            exec(compile(file.read(), filename=script_path, mode="exec"), globals_)
        return globals_["main"]

    def figure(self, script_name, *args, width=None, aspect=SQUARE, **kwargs):
        r"""Insert a figure from a Python script.

        The script should contain a function called `main`, which draws onto a
        pre-configured matplotlib figure and returns a unique name (without
        extension) for
        the figure.  The figure will then be saved and included as a PGF in the
        document.
        Any setup done in the document's pythontexcustomcode environment will be
        available.

        `main` will be called with any leftover arguments to this function.  The working
        directory will be the project directory, not the scripts directory.

        By default, the figure's filename will be the script name with the figure size
        appended.  To override this, return a string from `main`.  This is important if
        you use a drawing function several times with different arguments in the same
        document!

        Any files read in `main` should either be opened using `pytex.open` or passed to
        `pytex.add_dependencies` (so that pythontex re-runs the script when they
        change),
        and should be in `DATA_DIR` (so that latexmk triggers a build when they change).

        Any files written in `main` should either be opened using `pytex.open` or passed
        to `pytex.add_created` (so that pythontex deletes the old file when it is
        renamed),
        and should go in `FIGURES_DIR`, (so that latexmk removes them on clean).

        Args:
            script_name (str): The filename of the script (with or without extension),
                either as an absolute path or relative to the scripts directory.
            width (float): The figure width in inches (defaults to \textwidth).  For a
                fraction of \textwidth, use the TEXT_WIDTH constant (e.g.,
                0.5*TEXT_WIDTH).
            aspect (float): The figure aspect ratio (SQUARE, GOLDEN, or a number).

        Returns:
            str: The LaTeX markup which includes the figure in the document.
        """
        if width is None:
            width = self.text_width

        if not script_name.endswith(".py"):
            script_name += ".py"
        main = self._load_script(script_name)
        default_name = Path(script_name).stem
        figure_filename = _draw_figure(
            lambda: main(*args, **kwargs), width, aspect, output_dir=self.output_dir,
            default_name=default_name
        )

        self.pytex.add_created(figure_filename)
        return r"\input{%s}" % figure_filename


def _figure_tweaks():
    """Adjust figure before saving."""
    # From https://github.com/bcbnz/matplotlib-pgfutils/blob/ddd71596659718a8b55ca511a112df5ea1b5d7a8/pgfutils.py#L706  # noqa:B950
    for axes in plt.gcf().get_axes():
        # There is no rcParam for the legend border line width, so manually adjust it
        # to match the default axes border line width
        legend = axes.get_legend()
        if legend:
            frame = legend.get_frame()
            frame.set_linewidth(mpl.rcParams["axes.linewidth"])


def _pgf_tweaks(filename):
    """Adjust PGF file after saving."""
    pgf_text = open(filename).read()

    # Not sure precisely what the behaviour is, but sometimes axis labels get stuck sans
    # or sans-serif regardless of font.family.  Let's just remove all the font family
    # selection and match the document font.
    # TODO: Figure out exactly what causes this and report bug
    pgf_text = pgf_text.replace(r"\rmfamily", "")
    pgf_text = pgf_text.replace(r"\sffamily", "")

    # Regex which matches image commands, splitting the filename by extension
    pattern = re.compile(r"(\\(?:pgfimage|includegraphics)(?:\[.+?\])?{)([^}]+)(\..+?})")

    # From https://github.com/bcbnz/matplotlib-pgfutils/blob/de2b3651cf359da2263864238f81ed3a4a860d4a/pgfutils.py#L793  # noqa: B950
    if Path(filename).parent.absolute() != Path(".").absolute():
        # If the PGF file is not in the top-level directory (which it isn't by default),
        # fix the paths in \pgfimage and \includegraphics commands (for rasterised
        # plots).  I think matplotlib might have changed from one to the other at some
        # points.
        prefix = str(Path(filename).parent.relative_to("."))
        replacement = r"\1{0:s}/\2\3".format(prefix)
        pgf_text = re.sub(pattern, replacement, pgf_text)

    # Escape dots in image filenames
    pgf_text = re.sub(pattern, r"\1{\2}\3", pgf_text)

    open(filename, "w").write(pgf_text)


def _draw_figure(figure_func, width, aspect=1, output_dir=".", default_name=None, format_="pgf"):
    """Set up a matplotlib figure, call a function to draw in it, then save it in the
    given format and return the filename.

    Args:
        figure_func (Callable[[], str]): A function which takes no arguments, draws a
            figure, and returns a unique name for the figure.
        width (float): The figure width in inches.
        aspect (float): The figure aspect ratio.
        default_name (str): The filename to use if `figure_func` does not return one.
        format_ (str): The file format in which to save the figure ('pdf' or 'pgf').

    Returns:
        str: The saved figure's filename.
    """
    figure_size = (width, width / aspect)
    plt.figure(figsize=figure_size)

    # TODO: Stub out plt.figure
    # Run figure function, then reset mpl.rcParams
    with mpl.rc_context():
        name = figure_func()
    # Generate name for figure
    # TODO: Is this a sensible way to define the filename?
    if name is None:
        name = default_name
    assert name is not None
    name += "-%.2fx%.2f" % figure_size

    _figure_tweaks()

    assert Path(output_dir).is_dir(), "Output dir does not exist"
    figure_filename = Path(output_dir) / (name + "." + format_)
    # TODO: Check if already created this run
    plt.savefig(figure_filename, bbox_inches="tight")
    plt.close("all")

    if format_ == "pgf":
        _pgf_tweaks(figure_filename)

    return figure_filename


def run_standalone(main):
    """Turn the calling module into a standalone script which generates its figure.

    The setup code from the main document will be executed, but the pytex instance will
    not be available (so `pytex.open` etc will not work).  The figure will be generated
    as a 4x4" PDF in the current working directory.

    Args:
        main (Callable[..., str]: The `main` function from a figure script.
    """
    # TODO: Command-line arguments
    # TODO: Stub pytex.open etc
    print("Setting up...")
    setup_matplotlib()

    print("Drawing...")
    default_name = Path(main.__globals__["__file__"]).stem
    # TODO: Specify output path
    figure_filename = _draw_figure(
        main, width=4, default_name=default_name, format_="pdf"
    )
    print("Saved figure as", figure_filename)
