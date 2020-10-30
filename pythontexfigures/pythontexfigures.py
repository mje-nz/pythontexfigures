"""PythonTeX figure helpers.

Author: Matthew Edwards
Date: July 2019
"""
import math
import re
import string
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

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


def _calculate_figure_name(script: StrPath, args: Iterable, kwargs: dict):
    r"""Calculate the stem for a saved figure file, incorporating the arguments.

    Hopefully when combined with the figure size this is unique for a given call to
    \pyfig.

    Args:
        script: Filename of figure script
        args: Positional arguments to figure script
        kwargs: Keyword arguments to figure script
    """
    name = Path(script).stem
    parts = [str(arg) for arg in args] + [f"{k}-{v}" for k, v in kwargs.items()]
    valid_chars = "-_.," + string.ascii_letters + string.digits
    parts = ["".join(c for c in part if c in valid_chars) for part in parts]
    parts = [part for part in parts if part]
    if parts:
        name += "-" + "-".join(parts)
    return name


GOLDEN_RATIO = (1.0 + math.sqrt(5.0)) / 2.0


class TexHelper:
    r"""Implementation for \pyfig command."""

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
        """The text width from the PythonTeX context, in inches."""
        return self.pytex.pt_to_in(self.pytex.context.textwidth)

    @property
    def line_width(self):
        """The line width from the PythonTeX context, in inches."""
        return self.pytex.pt_to_in(self.pytex.context.linewidth)

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

    def _find_script(self, script_name: StrPath):
        """Find a figure script by name.

        The path from pythontexfigures is used.  With package option 'relative', the
        path is relative to the file being processed.

        Args:
            script_name: The filename of the script, either as an absolute path or
                relative to the script search path.

        Returns:
            Path: Script path.
        """
        script = Path(script_name)
        if script.is_absolute():
            # TODO: This seems like it misses the non-relative case
            assert script.exists()
            return script

        script_path = self.script_path / script
        assert (
            script_path.exists()
        ), f"Script {script_path} not found ({script_path.resolve()})"
        return script_path

    def _load_script(self, script_name: str) -> Callable:
        """Load the main() function from the given script.

        Args:
            script_name: The filename of the script, either as an absolute path or
                relative to the script search path.

        Returns:
            The main() function.
        """
        script_path = self._find_script(script_name)

        globals_: Dict[str, Any] = dict(
            __file__=str(script_path), __name__=script_path.stem
        )
        # https://stackoverflow.com/a/41658338
        with self.pytex.open(script_path, "rb") as file:
            exec(compile(file.read(), filename=script_path, mode="exec"), globals_)
        return globals_["main"]

    def _parse_pyfig_args(self, args_str: str):
        r"""Parse the arguments to a \pyfig command."""
        args = re.sub(r"golden(,|$)", f"aspect={GOLDEN_RATIO}", args_str)
        # Sometimes you need to use \textwidth{} instead of \textwidth to get the syntax
        # to work in the document, and then it comes through as the number followed by a
        # space then the braces.
        args = re.sub(r"(\d)\\textwidth(\s*{})?", rf"\1*{self.text_width}", args)
        args = re.sub(r"(\d)\\linewidth(\s*{})?", rf"\1*{self.line_width}", args)
        args = args.replace(r"\{", "{").replace(r"\}", "}")
        arg_evaluator = textwrap.dedent(
            f"""
            def get_args(*args, **kwargs):
                return args, kwargs
            args, kwargs = get_args({args})
            """
        )
        locals_: Dict[str, Any] = {}
        try:
            exec(compile(arg_evaluator, filename="<options>", mode="exec"), locals_)
        except SyntaxError as e:
            msg = f"Could not parse argument string {args_str} ({args})"
            raise ValueError(msg) from e
        return locals_["args"], locals_["kwargs"]

    def _do_figure(
        self, script_name, *args, width=None, height=None, aspect=None, **kwargs
    ):
        r"""Insert a figure from a Python script.

        The script should contain a function called `main`, which draws onto a
        pre-configured matplotlib figure and optionally returns a unique name (without
        extension) for the figure.  The figure will then be saved and included as a PGF
        in the document.  The figure's filename will be the script name with the
        arguments and figure size appended.

        `main` will be called with any leftover arguments to this function.  The working
        directory will be the directory from which `pythontex` is called, not the
        script's directory.

        TODO: this isn't possible any more
        Any files read in `main` should either be opened using `pytex.open` or passed to
        `pytex.add_dependencies` (so that pythontex re-runs the script when they
        change),
        and should be in `DATA_DIR` (so that latexmk triggers a build when they change).

        TODO: this isn't possible any more
        Any files written in `main` should either be opened using `pytex.open` or passed
        to `pytex.add_created` (so that pythontex deletes the old file when it is
        renamed),
        and should go in `FIGURES_DIR`, (so that latexmk removes them on clean).

        Returns:
            The LaTeX markup which includes the figure in the document.
        """
        if width is None:
            width = self.line_width
        if not script_name.endswith(".py"):
            script_name += ".py"

        main = self._load_script(script_name)
        figure_filename = _draw_figure(
            lambda: main(*args, **kwargs),
            _calculate_figure_name(script_name, args, kwargs),
            width=width,
            height=height,
            aspect=aspect,
            output_dir=self.output_dir,
        )

        self.pytex.add_created(figure_filename)
        return r"\input{%s}" % figure_filename

    def figure(self, script_name: str, options: str):
        r"""Perform a \pyfig command."""
        # Remove padding (see pythontexfigures.sty)
        script_name = script_name[1:-1]
        options = options[1:-1]

        # Remove quotes around script name if present
        script_name = script_name.strip("\"'")

        args, kwargs = self._parse_pyfig_args(options)
        return self._do_figure(script_name, *args, **kwargs)


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
    pattern = re.compile(
        r"(\\(?:pgfimage|includegraphics)(?:\[.+?\])?{)([^}]+)(\..+?})"
    )

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


def _draw_figure(
    figure_func: Callable,
    name: str,
    width: float,
    height: float = None,
    aspect: float = None,
    output_dir: StrPath = ".",
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
    if aspect is None:
        aspect = 1
    if height is None:
        height = width / aspect
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
    assert Path(output_dir).is_dir(), "Output dir does not exist"
    figure_filename = Path(output_dir) / (name + "." + format_)
    # TODO: Check if already created this run
    plt.savefig(figure_filename, bbox_inches="tight", pad_inches=0)
    plt.close("all")

    if format_ == "pgf":
        _pgf_tweaks(figure_filename)

    return figure_filename


def run_standalone(main: Callable):
    """Turn the calling module into a standalone script which generates its figure.

    The setup code from the main document will be executed, but the pytex instance will
    not be available (so `pytex.open` etc will not work).  The figure will be generated
    as a 4x4" PDF in the current working directory.

    Args:
        main: The `main` function from a figure script.
    """
    # TODO: Command-line arguments
    # TODO: Stub pytex.open etc
    setup_matplotlib()

    name = Path(main.__globals__["__file__"]).stem  # type: ignore
    # TODO: Specify output path
    figure_filename = _draw_figure(main, name, width=4, format_="pdf", verbose=True)
    print("Saved figure as", figure_filename)

    # TODO: tests
