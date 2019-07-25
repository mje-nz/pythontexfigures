"""PythonTeX figure helpers.

Author: Matthew Edwards
Date: July 2019
"""
import glob
import inspect
import math
import textwrap
from pathlib import Path
from typing import Callable, Optional

import matplotlib as mpl

# When generating PDF figures, use PGF backend so it looks the same as it will when
# called from LaTeX
mpl.use("pgf")
import matplotlib.pyplot as plt  # isort:skip

from .util import section_of_file  # isort:skip


SQUARE = 1
GOLDEN = (1.0 + math.sqrt(5.0)) / 2.0

# Placeholders for setup()
pytex = None
FONT_SIZE = None  # type: Optional[float]
TEXT_WIDTH = None  # type: Optional[float]
FIGURES_DIR = None  # type: Optional[str]


def _setup_paths():
    """Set default search path

    Args:
        scripts_dir (str): Directory containing figure scripts.
    """
    global FIGURES_DIR
    try:
        # Put figures in PythonTeX output directory
        FIGURES_DIR = pytex.context.outputdir
    except AttributeError:
        # In standalone mode, put figures in working directory
        FIGURES_DIR = "."

    assert FIGURES_DIR is not None, "No data directory defined"


def _setup_matplotlib(font_size=None):
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
            "pgf.preamble": [
                r"\usepackage[utf8x]{inputenc}",
                r"\usepackage[T1]{fontenc}",
            ],
        }
    )

    # Use default LaTeX fonts (to match appearance for PDFs, to get correct layout for
    # PGFs)
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [],
            "font.sans-serif": [],
            "font.monospace": [],
        }
    )

    # Set base font size
    if font_size is None and FONT_SIZE is not None:
        # Use document font size
        font_size = FONT_SIZE
    if font_size:
        mpl.rcParams["font.size"] = font_size

    # Make text a bit smaller (small is relative to font.size)
    # TODO: Use \footnotesize
    #       https://tex.stackexchange.com/questions/24599/what-point-pt-font-size-are-large-etc
    mpl.rcParams.update(
        {
            "axes.labelsize": "small",
            "axes.titlesize": "small",
            "figure.titlesize": "small",
            "legend.fontsize": "small",
            "xtick.labelsize": "small",
            "ytick.labelsize": "small",
        }
    )

    mpl.rcParams.update(
        {
            # Make axes border line width slightly thinner
            "axes.linewidth": 0.6,
            # Reduce legend label spacing slightly
            "legend.labelspacing": "0.3",
        }
    )


def setup(pytex_):
    """Configure matplotlib, resolve paths to figure scripts, and save pytex
    context.

    Call this at the start of the PythonTeX custom code, **before** importing
    matplotlib.

    Args:
        pytex_ (module): The global PythonTeXUtils instance.
    """
    global pytex, FONT_SIZE, TEXT_WIDTH

    # Save pytex reference
    assert pytex_ is not None
    pytex = pytex_

    # Re-run pythontex when files in this package change
    for path in sorted(Path(__file__).parent.iterdir()):
        if path.is_file():
            pytex.add_dependencies(path)

    # Save \fsize and \textwidth as "constants"
    FONT_SIZE = float(pytex.context.fontsize[:-2])
    TEXT_WIDTH = pytex.pt_to_in(pytex.context.textwidth)

    _setup_paths()
    _setup_matplotlib()


def print_preamble():
    r"""Print the contents of pythontexfigures.sty formatted to go in the preamble.

    If you don't have pythontexfigures.sty in your TeX tree, you can fudge it by
    calling this in your preamble and following with \printpythontex.
    """
    # Import this here so python -m pythontexfigures.sty behaves
    from .sty import sty_file_as_string

    print(r"\makeatletter")
    print(sty_file_as_string().splitlines()[2:])
    print(r"\makeatother")


def _find_script(script_name):
    """Find a figure script by name.

    TODO

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the script search path.
    Returns:
        Path: Script path
    """
    script_name = Path(script_name)
    if script_name.is_absolute():
        assert script_name.exists()
        return script_name

    current_file_dir = pytex.context.currdir
    script_subfolder = pytex.context.scriptpath

    if current_file_dir:
        # With the 'relative' package option, look for scripts relative to the file
        # being processed
        script_dir = Path(current_file_dir)
        if script_subfolder:
            script_subfolder = Path(script_subfolder)
            assert not script_subfolder.is_absolute()
    else:
        # Otherwise, look for scripts relative to the current working directory
        script_dir = Path()
    script_path = script_dir / script_subfolder / script_name
    # print('Script path:', script_path)
    script_path = script_path.resolve()
    assert script_path.exists()
    return script_path


def _load_script(script_name):
    """Load the main() function from the given script, such that it will run in the
    PythonTeX session's namespace.

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the script search path.

    Returns:
        Callable[..., str]: The main() function.
    """
    script_path = _find_script(script_name)

    # Copy the globals from the PythonTeX session's namespace (so imports from the setup
    # block are present), but set __file__ and __name__ such that it looks like it's
    # being imported normally.  Note that this will totally break if this function isn't
    # exactly two calls down from a PythonTeX environment.
    assert inspect.stack()[2].filename.startswith("pythontex-files-")
    globals_ = inspect.stack()[2].frame.f_globals.copy()
    globals_.update({"__file__": script_path, "__name__": script_name})

    # https://stackoverflow.com/a/41658338
    with pytex.open(script_path, "rb") as file:
        exec(compile(file.read(), filename=script_path, mode="exec"), globals_)
    return globals_["main"]


def _figure_tweaks():
    """Adjust figure before saving."""
    # From https://github.com/bcbnz/matplotlib-pgfutils/blob/ddd71596659718a8b55ca511a112df5ea1b5d7a8/pgfutils.py#L706
    for axes in plt.gcf().get_axes():
        # There is no rcParam for the legend border line width, so manually adjust it
        # to match the default axes border line width
        legend = axes.get_legend()
        if legend:
            frame = legend.get_frame()
            frame.set_linewidth(mpl.rcParams["axes.linewidth"])


def _pgf_tweaks(filename):
    """Adjust PGF file after saving."""
    # Not sure precisely what the behaviour is, but sometimes axis labels get stuck sans
    # or sans-serif regardless of font.family.  Let's just make remove all the font
    # family selection and match the document font.
    # TODO: Figure out exactly what causes this and report bug
    pgf_text = open(filename).read()
    pgf_text = pgf_text.replace(r"\rmfamily", "")
    pgf_text = pgf_text.replace(r"\sffamily", "")
    open(filename, "w").write(pgf_text)


def _draw_figure(figure_func, width, aspect, default_name=None, format_="pgf"):
    """Set up a matplotlib figure, call a function to draw in it, then save it in the
    given format and return the filename.

    Args:
        figure_func (Callable[[], str]): A function which takes no arguments, draws a
            figure, and returns a unique name for the figure.
        width (float): The figure width in inches.
        aspect (float): The figure aspect ratio.
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

    assert Path(FIGURES_DIR).is_dir(), "Figures dir does not exist"
    figure_filename = Path(FIGURES_DIR) / (name + "." + format_)
    # TODO: Check if already created this run
    plt.savefig(figure_filename, bbox_inches="tight")
    # TODO: Close figures?

    if format_ == "pgf":
        _pgf_tweaks(figure_filename)

    return figure_filename


def figure(script_name, *args, width=TEXT_WIDTH, aspect=SQUARE, **kwargs):
    r"""Insert a figure from a Python script.

    The script should contain a function called `main`, which draws onto a
    pre-configured matplotlib figure and returns a unique name (without extension) for
    the figure.  The figure will then be saved and included as a PGF in the document.
    Any setup done in the document's pythontexcustomcode environment will be available.
`
    `main` will be called with any leftover arguments to this function.  The working
    directory will be the project directory, not the scripts directory.

    By default, the figure's filename will be the script name with the figure size
    appended.  To override this, return a string from `main`.  This is important if
    you use a drawing function several times with different arguments in the same
    document!

    Any files read in `main` should either be opened using `pytex.open` or passed to
    `pytex.add_dependencies` (so that pythontex re-runs the script when they change),
    and should be in `DATA_DIR` (so that latexmk triggers a build when they change).

    Any files written in `main` should either be opened using `pytex.open` or passed
    to `pytex.add_created` (so that pythontex deletes the old file when it is renamed),
    and should go in `FIGURES_DIR`, (so that latexmk removes them on clean).

    Args:
        script_name (str): The filename of the script (with or without extension),
            either as an absolute path or relative to the scripts directory.
        width (float): The figure width in inches (defaults to \textwidth).  For a
            fraction of \textwidth, use the TEXT_WIDTH constant (e.g., 0.5*TEXT_WIDTH).
        aspect (float): The figure aspect ratio (SQUARE, GOLDEN, or a number).

    Returns:
        str: The LaTeX markup which includes the figure in the document.
    """
    if width is None:
        # TEXT_WIDTH is calculated when setup runs, so it doesn't actually work as a
        # default argument
        width = TEXT_WIDTH

    if not script_name.endswith(".py"):
        script_name += ".py"
    main = _load_script(script_name)
    default_name = Path(script_name).stem
    figure_filename = _draw_figure(
        lambda: main(*args, **kwargs), width, aspect, default_name=default_name
    )

    pytex.add_created(figure_filename)
    return r"\input{%s}" % figure_filename


def _run_setup_code(document_name, globals_):
    """Run the PythonTeX setup code from the given document in the given namespace.

    A .pytxcode file generated by PythonTeX is parsed to find the first custom code
    block, then the code is extracted and executed in the given namespace (except for
    calls to `setup`).

    Args:
        document_name (str): The name (with or without extension) of a tex document
            processed by PythonTeX which contains a pythontexcustomcode environment.
        globals_ (dict): The globals() dictionary from the namespace in which to run the
            setup code.
    """
    document_name = Path(document_name).stem
    pytxcode_file = document_name + ".pytxcode"
    assert Path(pytxcode_file).exists()

    # Find the pythontexcustomcode section
    custom_code_lines = section_of_file(
        pytxcode_file,
        lambda line: line.startswith("=>PYTHONTEX#CC:py:begin"),
        lambda line: line.startswith("=>PYTHONTEX"),
    )

    # Remove call to setup()
    # TODO: Handle setting figure/data paths
    custom_code_lines = [
        line for line in custom_code_lines if not line.strip().endswith(".setup(pytex)")
    ]

    # Execute
    custom_code = textwrap.dedent("".join(custom_code_lines))
    exec(compile(custom_code, filename="<pythontexcustomcode>", mode="exec"), globals_)


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
    # TODO: Specify somehow
    pytxcode_files = glob.glob("*.pytxcode")
    assert len(pytxcode_files) == 1
    _run_setup_code(pytxcode_files[0], main.__globals__)
    _setup_paths()
    _setup_matplotlib()

    print("Drawing...")
    default_name = Path(main.__globals__["__file__"]).stem
    figure_filename = _draw_figure(
        main, width=4, aspect=SQUARE, default_name=default_name, format_="pdf"
    )
    print("Saved figure as", figure_filename)
