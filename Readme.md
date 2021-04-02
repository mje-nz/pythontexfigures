# LaTeX Python figures

Given a Python script like this which draws a Matplotlib figure:
```python
# Test.py
import matplotlib.pyplot as plt
import numpy as np


def main():
    x = np.arange(10)
    y = x ** 2
    plt.plot(x, y)
    plt.xlabel("$x$")
    plt.ylabel("$x^2$")
```

you can insert it into a LaTeX document like this:

```latex
\begin{figure}
    \pyfig{test}
    \caption{Test figure.}
\end{figure}
```

The figure size defaults to `\linewidth` square, and the axis labels etc. use the document font with a default size of `\footnotesize`.

TODO: advanced examples


## Installation
Requires a LaTeX installation (probably TeX Live 2019), PythonTeX, and Python 3.6 or greater.
Examples require latexmk.

To install the Python package:
```bash
pip3 install pythontexfigures
```

To install the LaTeX package into `texmf-local`:
```bash
sudo python3 -m pythontexfigures.install
```
If you don't have root access, you can install it into `texmf-home` instead:
```bash
sudo python3 -m pythontexfigures.install TEXMFHOME
```

Alternatively, call `pf.print_preamble()` in your pythontexcustomcode and follow with `\printpythontex`.


## Troubleshooting
If you get `! TeX capacity exceeded, sorry [main memory size=5000000].`, then you should probably rasterize your figure (as recommended at the bottom of the [matplotlib PGF tutorial](https://matplotlib.org/tutorials/text/pgf.html)).


## Development
To install the Python package in editable mode:
```bash
pip3 install -e .
```

To link the LaTeX package into [your private tree](https://www.texfaq.org/FAQ-privinst):
```bash
export PF_DIR=$(kpsewhich -var-value=TEXMFHOME)/tex/latex/pythontexfigures
mkdir -p $PF_DIR
ln -s $(pwd)/pythontexfigures/pythontexfigures.sty $PF_DIR/
```

Use [pre-commit](https://pre-commit.com) to check and format changes before committing:
```bash
pip install pre-commit
pre-commit install
```


## Misc

Wishlist:

* Better documentation
* More tests
* Inline figures
* Tables
* One session per figure
* Coverage
* Sort out and test non-clean builds
* TODO: Why are the left and/or bottom axis borders thicker sometimes?
* TODO: convince `latexmk` that `pdflatex` should always run before `pythontex` if
  both need to run
* Sensible way of doing relative imports from inside figure scripts
* TODO: do failed scripts ever get re-run?
* TODO: Figure out why pythontex has stopped running at all in latexmk

Tested with PythonTeX 0.16, and latexmk 4.63b.
Note that PythonTeX 0.16 is quite outdated; a patch is included for one issue which is fixed upstream but not yet released.
TODO: this isn't true any more, test 0.17.
Inspired by [TheChymera/RepSeP](https://github.com/TheChymera/RepSeP) (but much simpler) and [this blog post by Bennett Kanuka](http://bkanuka.com/posts/native-latex-plots/) (but more automated).
A few bits borrowed from Blair Bonnet's [matplotlib-pgfutils](https://github.com/bcbnz/matplotlib-pgfutils).
