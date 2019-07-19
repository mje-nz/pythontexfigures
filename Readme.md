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

Wishlist:

* Better Readme
* Tests
* CI
* Inline figures
* Tables

Tested with Python 3.7, matplotlib 3.0.3, PythonTeX 0.16, and latexmk 4.63b.
Note that PythonTeX 0.16 is quite outdated; `example.tex` includes a patch for one issue which is fixed upstream but not yet released.
Inspired by [TheChymera/RepSeP](https://github.com/TheChymera/RepSeP) (but much simpler) and [this blog post by Bennett Kanuka](http://bkanuka.com/posts/native-latex-plots/) (but more automated).
