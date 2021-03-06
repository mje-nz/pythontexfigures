"""Very simple test figure.

Author: Matthew Edwards
Date: July 2019
"""

import matplotlib.pyplot as plt
import numpy as np


def main():
    """Draw x**2 over [0, 10]."""
    x = np.linspace(0, 10, 100)
    y = x ** 2
    plt.plot(x, y, label="$x^2$")
    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.legend()


if __name__ == "__main__":
    import pythontexfigures as ptf

    ptf.run_standalone(main)
