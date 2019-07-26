"""Very simple test figure.

Author: Matthew Edwards
Date: July 2019
"""


def main():
    """Draw x**2 on [0, 10]."""
    x = np.linspace(0, 10, 100)
    y = x ** 2
    plt.plot(x, y, label="$x^2$")
    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.legend()
    return "test"  # Figure filename


if __name__ == "__main__":
    import pythontexfigures as pf

    pf.run_standalone(main)
