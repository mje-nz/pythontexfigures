import math
import os
import os.path

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('white')


SQUARE = 1
GOLDEN = (1.0 + math.sqrt(5.0))/2.0


# https://stackoverflow.com/a/41658338
def load_script(script_name):
    """Load the main() function from the given script.

    Args:
        script_name (str): The filename of the script, either as an absolute path or
            relative to the scripts directory.
    """
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    globals_ = globals().copy()
    globals_.update({
        "__file__": script_path,
        "__name__": script_name,
    })
    with pytex.open(script_path, 'rb') as file:
        exec(compile(file.read(), filename=script_path, mode='exec'), globals_)
    return globals_['main']


def textwidth():
    r"""Return the document's \textwidth in inches, to use in matplotlib figsize."""
    # Would be nice to just have this as a global constant, but pytex.context isn't
    # in pythontexcustomcode environments in PythonTeX 0.16
    # https://github.com/gpoore/pythontex/issues/65
    try:
        return pytex.pt_to_in(pytex.context.textwidth)
    except NameError:
        # Continue quietly when running outside pythontex (but explode if
        # multiplied)
        return None


def python_fig(script, *args, width=None, aspect=SQUARE, **kwargs):
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
    assert 'pytex' in globals()

    if width is None:
        width = textwidth()
    figsize = (width, width/aspect)
    plt.figure(figsize=figsize)

    main = load_script(script)
    name = main(*args, **kwargs)
    assert name is not None
    name += '-%sx%s' % figsize

    if not os.path.isdir(FIGURES_DIR):
        os.mkdir(FIGURES_DIR)
    figure_filename = os.path.join(FIGURES_DIR, name + '.pgf')
    plt.savefig(figure_filename, bbox_inches='tight')
    pytex.add_created(figure_filename)
    return r'\input{%s}' % figure_filename
