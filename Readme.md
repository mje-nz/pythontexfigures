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

Tested with Python 3.7, matplotlib 3.0.3, PythonTeX 0.16, and latexmk 4.63b.
Inspired by [TheChymera/RepSeP](https://github.com/TheChymera/RepSeP) but much simpler.
