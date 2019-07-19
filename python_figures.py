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

import matplotlib as mpl
import matplotlib.pyplot as plt


SQUARE = 1
GOLDEN = (1.0 + math.sqrt(5.0))/2.0

# Placeholders for setup()
pytex = None
FONT_SIZE = None
TEXT_WIDTH = None
SCRIPTS_DIR = None
DATA_DIR = None
FIGURES_DIR = None


def _setup_paths(scripts_dir=None, data_dir=None, figures_dir=None):
    """Parse latexmkrc for path definitions, optionally overriding with arguments.

    Args:
        scripts_dir (str): Directory containing figure scripts (overrides latexmkrc)
        data_dir (str): Directory containing figure data files (overrides latexmkrc)
        figures_dir (str): Directory in which to save generated figures (overrides latexmkrc)
    """
    global SCRIPTS_DIR, DATA_DIR, FIGURES_DIR

    # Look for $pythontex_scripts_dir etc in latexmkrc
    if os.path.exists('latexmkrc'):
        regex = re.compile(r"\$pythontex_(\w*?)_dir = [\'\"](\w*?)[\'\"];$")
        with open('latexmkrc') as latexmkrc:
            for line in latexmkrc.readlines():
                line = line.strip()
                match = regex.search(line)
                if match:
                    dir_type, dir_name = match.groups()
                    if dir_type == 'scripts':
                        SCRIPTS_DIR = dir_name
                    elif dir_type == 'data':
                        DATA_DIR = dir_name
                    elif dir_type == 'figures':
                        FIGURES_DIR = dir_name
                    else:
                        print("Warning: unrecognised PythonTeX folder in latexmkrc (%s)" % line)

    # Override directories from latexmkrc with arguments if provided
    if scripts_dir is not None:
        SCRIPTS_DIR = scripts_dir
    if data_dir is not None:
        DATA_DIR = data_dir
    if figures_dir is not None:
        FIGURES_DIR = figures_dir

    # TODO: Error if undefined?
    # TODO: Put generated figures in pytex output directory?


def _setup_matplotlib(font_size=None):
    """Set up matplotlib.

    Args:
        font_size (float): Override base font size (in pt), defaults to document's font
            size (or matplotlib default in standalone mode).
    """
    # When generating PDF figures, use PGF backend so it looks the same as it will when
    # called from LaTeX
    mpl.use('pgf')
    mpl.rcParams.update({
        # Use pdflatex instead of xelatex in PGF backend
        "pgf.texsystem": "pdflatex",
        # Use LaTeX instead of mathtext for all text rendering
        "text.usetex": True,
        # Fix input and font encoding for PGF backend
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


def setup(pytex_, *, scripts_dir=None, data_dir=None, figures_dir=None):
    """Set up module (call before importing pyplot!)

    TODO

    By default the directories configured in latexmkrc are used, but you can override
    them here.

    Args:
        pytex_ (module): The global PythonTeXUtils instance
        scripts_dir (str): Directory containing figure scripts (overrides latexmkrc)
        data_dir (str): Directory containing figure data files (overrides latexmkrc)
        figures_dir (str): Directory in which to save generated figures (overrides latexmkrc)
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

    _setup_paths(scripts_dir, data_dir, figures_dir)
    _setup_matplotlib()


# https://stackoverflow.com/a/41658338
def _load_script(script_name):
    """Load the main() function from the given script.

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the scripts directory.
    """
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    # Copy the globals from the main pytex namespace (so imports from the setup block
    # are present), but set __file__ and __name__ such that it looks like it's being
    # imported normally.  Note that this will totally break if this function isn't
    # exactly two calls down from a PythonTeX environment.
    assert inspect.stack()[2].filename.startswith('pythontex-files-')
    globals_ = inspect.stack()[2].frame.f_globals.copy()
    globals_.update({
        "__file__": script_path,
        "__name__": script_name,
    })

    with pytex.open(script_path, 'rb') as file:
        exec(compile(file.read(), filename=script_path, mode='exec'), globals_)
    return globals_['main']


def _render_figure(figure_func, width, aspect, format_='pgf'):
    """Actually render the figure, without any PythonTeX-specific tricks."""
    figsize = (width, width/aspect)
    plt.figure(figsize=figsize)

    # Run figure function, then reset mpl.rcParams
    with mpl.rc_context():
        name = figure_func()
    # Generate name for figure
    # TODO: Is this a sensible way to define the filename?
    assert name is not None
    name += '-%.2fx%.2f' % figsize

    if not os.path.isdir(FIGURES_DIR):
        os.mkdir(FIGURES_DIR)
    figure_filename = os.path.join(FIGURES_DIR, name + '.' + format_)
    plt.savefig(figure_filename, bbox_inches='tight')
    return figure_filename


def figure(script_name, *args, width=TEXT_WIDTH, aspect=SQUARE, **kwargs):
    r"""Insert a figure from a Python script.

    The script will be executed as if imported from inside the scripts directory, but
    with numpy etc already in the global namespace.  Before main is executed, a figure
    of appropriate size is created.  After main returns, the figure will be saved and
    inserted into the document.

    Leftover positional and keyword arguments will be passed to main.  Main should
    return a unique filename (without extension).  Any files accessed in main should
    either be opened using pytex.open or passed to pytex.add_dependencies or
    pytex.add_created.

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the scripts directory.
        width (float): The figure width in inches (defaults to \textwidth).  For a
            fraction of \textwidth, use e.g. 0.5*textwidth()
        aspect (float): The figure aspect ratio (SQUARE, GOLDEN, or a number).
    """
    if width is None:
        # TEXT_WIDTH is calculated  when setup runs, so it doesn't actually work as a
        # default argument
        width = TEXT_WIDTH

    main = _load_script(script_name)
    figure_filename = _render_figure(lambda: main(*args, **kwargs), width, aspect)

    pytex.add_created(figure_filename)
    return r'\input{%s}' % figure_filename


def _run_setup_code(pytxcode_file, globals_):
    """Run the setup code in the given namespace to get the right imports."""
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
    # Remove call to setup()
    custom_code_lines = [line for line in lines[start_index:end_index] if not line.strip().endswith('.setup(pytex)')]
    # Execute
    custom_code = textwrap.dedent(''.join(custom_code_lines))
    exec(compile(custom_code, filename='<pythontexcustomcode>', mode='exec'), globals_)


def run_standalone(main):
    """Turn the calling module into a standalone script which generates its figure."""
    # TODO: Command-line arguments
    print('Setting up...')
    _run_setup_code('example.pytxcode', main.__globals__)
    _setup_paths()
    _setup_matplotlib()

    print('Drawing...')
    figure_filename = _render_figure(main, width=4, aspect=SQUARE, format_='pdf')
    print('Saved figure as', figure_filename)
