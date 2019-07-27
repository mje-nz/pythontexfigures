"""Draw an image.

Author: Matthew Edwards
Date: July 2019
"""


def main(size=1000):
    """Plot sin(x)*cos(y)."""
    # https://jakevdp.github.io/PythonDataScienceHandbook/04.07-customizing-colorbars.html
    x = np.linspace(0, 3 * np.pi, size)
    intensity = np.sin(x) * np.cos(x[:, np.newaxis])
    plt.imshow(intensity, cmap="RdYlGn")
    plt.xlabel("$x$")
    plt.ylabel("$y$")
    plt.colorbar(fraction=0.046, pad=0.04, label="Intensity")
    plt.tight_layout()


if __name__ == "__main__":
    import pythontexfigures as pf

    pf.run_standalone(main)
