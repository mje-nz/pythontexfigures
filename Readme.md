# LaTeX Python figures

Given a Python script like this which draws a Matplotlib figure:
```python
def main():
    x = np.arange(10)
    y = x**2
    plt.plot(x, y)
    plt.xlabel('$x$')
    plt.ylabel('$x^2$')
    return 'test'  # Figure filename
```

you can insert it into a LaTeX document like this:

```latex
\begin{figure}
    \pyfig{'test.py'}
    \caption{Test figure.}
\end{figure}
```

By default, the figure size defaults to `\textwidth` square and the font and font size match the rest of the document.



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


## Development
To install the Python package in editable:
```bash
pip3 install -e .
```

To link the LaTeX package into `texmf-local`:
```bash
export PF_DIR=$(kpsewhich -var-value=TEXMFLOCAL)/tex/latex/pythontexfigures
sudo mkdir -p $PF_DIR
sudo ln -s $(pwd)/pythontexfigures/pythontexfigures.sty $PF_DIR/
sudo mktexlsr
```


## Misc

Wishlist:

* Better documentation
* More tests
* Inline figures
* Tables
* One session per figure
* Test rasterisation
* Support for subfiles package

Tested with PythonTeX 0.16, and latexmk 4.63b.
Note that PythonTeX 0.16 is quite outdated; a patch is included for one issue which is fixed upstream but not yet released.
Inspired by [TheChymera/RepSeP](https://github.com/TheChymera/RepSeP) (but much simpler) and [this blog post by Bennett Kanuka](http://bkanuka.com/posts/native-latex-plots/) (but more automated).
