"""PythonTeX interface code.

Figure scripts should contain a function called `main`, which draws onto a
pre-configured matplotlib figure and optionally returns a unique name (without
extension) for the figure.  The working directory will be the directory from which
`pythontex` is called, not the script's directory.  The figure will then be saved and
included as a PGF in the LaTeX document.  The figure's filename will be the script name
with the arguments and figure size appended.

TODO: this isn't possible any more
Any files read in `main` should either be opened using `pytex.open` or passed to
`pytex.add_dependencies` (so that pythontex re-runs the script when they change), and
should be in `DATA_DIR` (so that latexmk triggers a build when they change).

TODO: this isn't possible any more
Any files written in `main` should either be opened using `pytex.open` or passed to
`pytex.add_created` (so that pythontex deletes the old file when it is renamed), and
should go in `FIGURES_DIR`, (so that latexmk removes them on clean).
"""
import math
import string
import textwrap
from functools import partial
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Optional

from attr import attrs

from .drawing import draw_figure, setup_matplotlib
from .util import StrPath


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


def evaluate_arg_str(args: str):
    """Evaluate a Python argument string into an args tuple and kwargs dict."""
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
        msg = f"Could not parse argument string {args}"
        raise ValueError(msg) from e
    return locals_["args"], locals_["kwargs"]


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

    def pretty(self):
        """Return a string representation for debugging."""
        keys = ("font_size", "text_width", "line_width", "output_dir", "script_path")
        props = ", ".join(f"{key}={getattr(self, key)!r}" for key in keys)
        return f"TexHelper({props})"

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
        exec(f"import sys; sys.path.append('{str(script_path.parent)}')", globals_)
        # https://stackoverflow.com/a/41658338
        with self.pytex.open(script_path, "rb") as file:
            exec(compile(file.read(), filename=script_path, mode="exec"), globals_)
        return globals_["main"]

    def _evaluate_units(self, arg):
        """Evaluate units in a height or width specification."""
        arg = arg.strip()
        if arg.endswith("{}"):
            # Sometimes you need to use \textwidth{} instead of \textwidth to get the
            # syntax to work in the document, and then it comes through as the command
            # followed by a space then the braces.
            # TODO: is this still true with xparse?
            arg = arg[:-2].strip()
        units = (
            ("pt", 1),
            ("in", 72.27),
            ("cm", 72.27 / 2.54),
            ("mm", 72.27 / 25.4),
            (r"\textwidth", self.text_width),
            (r"\linewidth", self.line_width),
        )
        for unit, size_in_pt in units:
            if arg.endswith(unit):
                return float(arg[: -len(unit)]) * size_in_pt
        return float(arg) * self.line_width

    def _parse_pyfig_options(self, args_str: str):
        r"""Parse the options for a \pyfig command.

        Returns:
            width, height, dict of any other arguments
        """
        params = {}  # type: Dict[str, Any]
        args = [arg for arg in args_str.split(",") if arg]
        keyval_args = [arg for arg in args if "=" in arg]
        val_args = [arg for arg in args if "=" not in arg]

        # First take key=value args
        for arg in keyval_args:
            key, val = arg.split("=")
            key = key.strip()
            if key not in ("width", "height", "aspect"):
                raise ValueError(f"Unknown key {key} ({args_str})")
            params[key] = val

        # Special-case "golden"
        if "golden" in val_args:
            params["aspect"] = GOLDEN_RATIO
            val_args.remove("golden")

        # Then fill in missing params from value-only args
        for key in ("width", "height"):
            if key not in params and val_args:
                params[key] = val_args.pop(0)
        if val_args:
            raise ValueError(f"Left-over arguments {val_args} ({args_str})")

        # Evaluate units in width and height
        for key in ("width", "height"):
            if key in params:
                params[key] = self._evaluate_units(params[key])

        # Calculate width and height
        width = params.pop("width", self.line_width)
        aspect = float(params.pop("aspect", 1))
        height = params.pop("height", width / aspect)
        return width, height, params

    def figure(self, script_name: str, figure_options: str, script_args: str):
        r"""Perform a \pyfig command."""
        # Remove padding (see pythontexfigures.sty)
        script_name = script_name[1:-1]
        figure_options = figure_options[1:-1]
        script_args = script_args[1:-1]

        # Remove quotes around script name if present
        script_name = script_name.strip("\"'")

        if not script_name.endswith(".py"):
            script_name += ".py"

        width, height, kwargs = self._parse_pyfig_options(figure_options)
        context = FigureContext(self, script_name, width, height, **kwargs)

        args, kwargs = evaluate_arg_str(script_args)
        return context.draw_and_include(*args, **kwargs)


def with_context(f):
    """Decorator for figure functions which enables passing the figure context."""
    f.use_context = True
    return f


@attrs(auto_attribs=True)
class FigureContext:
    """Drawing context for an individual figure."""

    helper: Optional[TexHelper]
    script_name: str
    width: float
    height: float

    # These are for run_standalone
    # TODO: support pdf figures through pyfig
    format_: str = "pgf"
    verbose: bool = False
    figure_func: Optional[Callable] = None
    output_dir: Optional[str] = None

    def __attrs_post_init__(self):
        """Fill in missing arguments from helper."""
        if self.width is None:
            self.width = self.helper.line_width
        if self.figure_func is None:
            self.figure_func = self.helper._load_script(self.script_name)
        if hasattr(self.figure_func, "use_context") and self.figure_func.use_context:
            self.figure_func = partial(self.figure_func, self)
        if self.output_dir is None and self.helper is not None:
            self.output_dir = self.helper.output_dir

    def draw(self, *args, **kwargs):
        """Draw the figure and return the filename."""
        figure_filename = draw_figure(
            lambda: self.figure_func(*args, **kwargs),
            _calculate_figure_name(self.script_name, args, kwargs),
            width=self.width,
            height=self.height,
            output_dir=self.output_dir,
            format_=self.format_,
        )

        if self.helper:
            self.helper.pytex.add_created(figure_filename)
        return figure_filename

    def _add_header_to_pgf(self, filename):
        """Add a header to the generated PGF file with debug information."""
        assert self.format_ == "pgf"

        header = "%% Generated by pythontexfigures\n"
        # TODO: add version
        header += f"%% Figure context: {self}\n"
        if self.helper:
            header += f"%% Tex context: {self.helper.pretty()}\n"
        header += "\n"

        file = Path(filename)
        pgf_text = file.read_text()
        file.write_text(header + pgf_text)

    def draw_and_include(self, *args, **kwargs):
        """Draw the figure and return the LaTeX code to include it."""
        figure_filename = self.draw(*args, **kwargs)
        assert self.format_ == "pgf"
        self._add_header_to_pgf(figure_filename)
        return r"\input{%s}" % figure_filename


def run_standalone(main: Callable):
    """Turn the calling module into a standalone script which generates its figure.

    The figure will be generated as a 4x4" PDF in the current working directory.

    Args:
        main: The `main` function from a figure script.
    """
    # TODO: Command-line arguments
    # TODO: Stub pytex.open etc
    setup_matplotlib()

    helper = None
    name = main.__globals__["__file__"]  # type: ignore
    ctx = FigureContext(
        helper, name, 4, 4, format_="pdf", verbose=True, figure_func=main
    )
    # TODO: Specify output path
    figure_filename = ctx.draw()
    print("Saved figure as", figure_filename)

    # TODO: tests
