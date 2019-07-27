"""Plot a polynomial.

Author: Matthew Edwards
Date: July 2019
"""
import numpy as np


def main(c, x=np.linspace(-5, 5, 100)):  # noqa: B008
    """Draw a polynomial."""
    y = np.polyval(c, x)
    label = (
        "$"
        + " + ".join(f"{ci}x^{len(c) - 1 - i}" for i, ci in enumerate(c) if ci != 0)
        + "$"
    )
    plt.plot(x, y, label=label)
    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.legend()
    return "polynomial-" + "-".join(str(ci) for ci in c)  # Figure filename


if __name__ == "__main__":
    import pythontexfigures as pf

    pf.run_standalone(main)
