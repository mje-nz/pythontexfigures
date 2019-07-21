"""PythonTeX figure helpers.

Author: Matthew Edwards
Date: July 2019
"""
import inspect
import math
import os
import os.path
import re
import textwrap
from typing import Callable, Optional

import matplotlib as mpl
# When generating PDF figures, use PGF backend so it looks the same as it will when
# called from LaTeX
mpl.use('pgf')
import matplotlib.pyplot as plt

from .sty import sty_file_as_string


SQUARE = 1
GOLDEN = (1.0 + math.sqrt(5.0))/2.0

# Placeholders for setup()
pytex = None
FONT_SIZE = None  # type: Optional[float]
TEXT_WIDTH = None  # type: Optional[float]
SCRIPTS_DIR = None  # type: Optional[str]
DATA_DIR = None  # type: Optional[str]
FIGURES_DIR = None  # type: Optional[str]


def _setup_paths(scripts_dir=None, data_dir=None):
    """Parse latexmkrc for path definitions, optionally overriding with arguments.

    Args:
        scripts_dir (str): Directory containing figure scripts (overrides latexmkrc).
        data_dir (str): Directory containing figure data files (overrides latexmkrc).
    """
    global SCRIPTS_DIR, DATA_DIR, FIGURES_DIR

    # Look for $pythontex_scripts_dir etc in latexmkrc
    if os.path.exists('latexmkrc'):
        regex = re.compile(r"\$pythontex_(\w*?)_dir = [\'\"](\w*?)[\'\"];$")
        with open('latexmkrc') as latexmkrc:
            for line in latexmkrc:
                line = line.strip()
                match = regex.search(line)
                if match:
                    dir_type, dir_name = match.groups()
                    if dir_type == 'scripts':
                        SCRIPTS_DIR = dir_name
                    elif dir_type == 'data':
                        DATA_DIR = dir_name
                    else:
                        print("Warning: unrecognised PythonTeX folder in latexmkrc (%s)" % line)

    # Override directories from latexmkrc with arguments if provided
    if scripts_dir is not None:
        SCRIPTS_DIR = scripts_dir
    if data_dir is not None:
        DATA_DIR = data_dir

    try:
        # Put figures in PythonTeX output directory
        FIGURES_DIR = pytex.context.outputdir
    except AttributeError:
        # In standalone mode, put figures in working directory
        FIGURES_DIR = "."

    assert SCRIPTS_DIR is not None, "No scripts directory defined"
    assert DATA_DIR is not None, "No data directory defined"
    assert FIGURES_DIR is not None, "No data directory defined"


def _setup_matplotlib(font_size=None):
    """Set up matplotlib.

    Args:
        font_size (float): Override base font size (in pt), defaults to document's font
            size (or matplotlib default in standalone mode).
    """
    # Set up PGF backend
    mpl.rcParams.update({
        # Use pdflatex instead of xelatex
        "pgf.texsystem": "pdflatex",
        # Use LaTeX instead of mathtext for all text rendering
        "text.usetex": True,
        # Fix input and font encoding
        "pgf.preamble": [
            r"\usepackage[utf8x]{inputenc}",
            r"\usepackage[T1]{fontenc}"
        ]
    })

    # Use default LaTeX fonts (to match appearance for PDFs, to get correct layout for
    # PGFs)
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": [],
        "font.sans-serif": [],
        "font.monospace": []
    })

    # Set base font size
    if font_size is None and FONT_SIZE is not None:
        # Use document font size
        font_size = FONT_SIZE
    if font_size:
        mpl.rcParams['font.size'] = font_size

    # Make legend and tick labels a bit smaller (small is relative to font.size)
    mpl.rcParams.update({
        "legend.fontsize": 'small',
        "xtick.labelsize": 'small',
        "ytick.labelsize": 'small'
    })


def setup(pytex_, *, scripts_dir=None, data_dir=None):
    """Configure matplotlib, resolve paths to figure scripts and data, and save pytex
    context.

    Call this at the start of the PythonTeX custom code, **before** importing
    matplotlib.

    By default the script/data directories from latexmkrc are used, but you can set them
    here instead if necessary.

    Args:
        pytex_ (module): The global PythonTeXUtils instance.
        scripts_dir (str): Directory containing figure scripts (overrides latexmkrc).
        data_dir (str): Directory containing figure data files (overrides latexmkrc).
    """
    global pytex, FONT_SIZE, TEXT_WIDTH

    # Save pytex reference
    assert pytex_ is not None
    pytex = pytex_

    # Re-run pythontex when this file changes
    pytex.add_dependencies(__file__)

    # Save \fsize and \textwidth as "constants"
    FONT_SIZE = float(pytex.context.fontsize[:-2])
    TEXT_WIDTH = pytex.pt_to_in(pytex.context.textwidth)

    _setup_paths(scripts_dir, data_dir)
    _setup_matplotlib()


def print_preamble():
    r"""Print the contents of pythontexfigures.sty formatted to go in the preamble.
    
    If you don't have pythontexfigures.sty in your TeX tree, you can fudge it by
    calling this in your preamble and following with \printpythontex.
    """
    print(r'\makeatletter')
    print(sty_file_as_string().splitlines()[2:])
    print(r'\makeatother')


def _load_script(script_name):
    """Load the main() function from the given script, such that it will run in the
    PythonTeX session's namespace.

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the scripts directory.

    Returns:
        Callable[..., str]: The main() function.
    """
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    # Copy the globals from the PythonTeX session's namespace (so imports from the setup
    # block are present), but set __file__ and __name__ such that it looks like it's
    # being imported normally.  Note that this will totally break if this function isn't
    # exactly two calls down from a PythonTeX environment.
    assert inspect.stack()[2].filename.startswith('pythontex-files-')
    globals_ = inspect.stack()[2].frame.f_globals.copy()
    globals_.update({
        "__file__": script_path,
        "__name__": script_name,
    })

    # https://stackoverflow.com/a/41658338
    with pytex.open(script_path, 'rb') as file:
        exec(compile(file.read(), filename=script_path, mode='exec'), globals_)
    return globals_['main']


def _draw_figure(figure_func, width, aspect, format_='pgf'):
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
    figure_size = (width, width/aspect)
    plt.figure(figsize=figure_size)

    # TODO: Stub out plt.figure
    # Run figure function, then reset mpl.rcParams
    with mpl.rc_context():
        name = figure_func()
    # Generate name for figure
    # TODO: Is this a sensible way to define the filename?
    assert name is not None
    name += '-%.2fx%.2f' % figure_size

    assert os.path.isdir(FIGURES_DIR), "Figures dir does not exist"
    figure_filename = os.path.join(FIGURES_DIR, name + '.' + format_)
    plt.savefig(figure_filename, bbox_inches='tight')
    # TODO: Close figures?
    return figure_filename


def figure(script_name, *args, width=TEXT_WIDTH, aspect=SQUARE, **kwargs):
    r"""Insert a figure from a Python script.

    The script should contain a function called `main`, which draws onto a
    pre-configured matplotlib figure and returns a unique name (without extension) for
    the figure.  The figure will then be saved and included as a PGF in the document.
    Any setup done in the document's pythontexcustomcode environment will be available.

    `main` will be called with any leftover arguments to this function.

    Any files read in `main` should either be opened using `pytex.open` or passed to
    `pytex.add_dependencies` (so that pythontex re-runs the script when they change),
    and should be in `DATA_DIR` (so that latexmk triggers a build when they change).

    Any files written in `main` should either be opened using `pytex.open` or passed
    to `pytex.add_created` (so that pythontex deletes the old file when it is renamed),
    and should go in `FIGURES_DIR`, (so that latexmk removes them on clean).

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the scripts directory.
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

    main = _load_script(script_name)
    figure_filename = _draw_figure(lambda: main(*args, **kwargs), width, aspect)

    pytex.add_created(figure_filename)
    return r'\input{%s}' % figure_filename


def _run_setup_code(document_name, globals_):
    """Run the PythonTeX setup code from the given document in the given namespace.

    A .pytxcode file generated by PythonTeX is parsed to find the first custom code
    block, then the code is extracted and executed in the given namespace (except for
    calls to `setup`).

    Args:
        document_name (str): The name (excluding extension) of a tex document processed
            by PythonTeX which contains a pythontexcustomcode environment.
        globals_ (dict): The globals() dictionary from the namespace in which to run the
            setup code.
    """
    document_name = os.path.basename(document_name)
    pytxcode_file = document_name + '.pytxcode'
    assert os.path.exists(pytxcode_file)

    with open(pytxcode_file, 'r') as pytxcode:
        lines = pytxcode.readlines()
    # Find the pythontexcustomcode section
    start_index = None
    for i, line in enumerate(lines):
        if line.startswith('=>PYTHONTEX#CC:py:begin'):
            # Custom code starts from the next line
            start_index = i + 1
            break
    assert start_index is not None
    end_index = None
    for i, line in enumerate(lines[start_index:]):
        if line.startswith('=>PYTHONTEX'):
            # Custom code ends at this line
            end_index = start_index + i
            break
    assert end_index is not None
    custom_code_lines = lines[start_index:end_index]

    # Remove call to setup()
    # TODO: Handle setting figure/data paths
    custom_code_lines = [line for line in custom_code_lines
                         if not line.strip().endswith('.setup(pytex)')]

    # Execute
    custom_code = textwrap.dedent(''.join(custom_code_lines))
    exec(compile(custom_code, filename='<pythontexcustomcode>', mode='exec'), globals_)


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
    print('Setting up...')
    # TODO: Not hard-coded
    _run_setup_code('example', main.__globals__)
    _setup_paths()
    _setup_matplotlib()

    print('Drawing...')
    figure_filename = _draw_figure(main, width=4, aspect=SQUARE, format_='pdf')
    print('Saved figure as', figure_filename)
