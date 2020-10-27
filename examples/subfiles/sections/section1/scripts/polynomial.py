"""Plot a polynomial.

Author: Matthew Edwards
Date: July 2019
"""
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

sns.set_style("white")


DEFAULT_X = np.linspace(-5, 5, 100)


def main(c=(1, 0, 0), x=DEFAULT_X):
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

    filename = "polynomial-" + "-".join(str(ci) for ci in c)
    return filename


if __name__ == "__main__":
    import pythontexfigures as ptf

    ptf.run_standalone(main)
