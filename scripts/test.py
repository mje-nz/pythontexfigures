"""Very simple test figure.

Author: Matthew Edwards
Date: July 2019
"""

def main():
    x = np.arange(10)
    y = x**2
    plt.plot(x, y)
    plt.xlabel('$x$')
    plt.ylabel('$x^2$')
    return 'test'  # Figure filename

# TODO: Wrapper for running from the command line
