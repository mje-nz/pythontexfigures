"""Plot a polynomial.

Author: Matthew Edwards
Date: July 2019
"""
from typing import Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np

DEFAULT_X = np.linspace(-5, 5, 100)


def main(coefficients: Sequence = (1, 0, 0), x: Iterable = DEFAULT_X):
    """Draw a polynomial.

    Args:
        coefficients: Coefficients of polynomial in descending order.
        x: Vector of x-values at which to evaluate the polynomial (default is -5 to 5).
    """
    y = np.polyval(coefficients, x)
    label = (
        "$"
        + " + ".join(
            f"{ci}x^{len(coefficients) - 1 - i}"
            for i, ci in enumerate(coefficients)
            if ci != 0
        )
        + "$"
    )
    plt.plot(x, y, label=label)
    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.legend()


if __name__ == "__main__":
    import pythontexfigures as ptf

    ptf.run_standalone(main)
