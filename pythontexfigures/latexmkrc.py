"""Wrapper for reading latexmkrc from wherever it gets packaged.

Author: Matthew Edwards
Date: July 2019
"""

from pathlib import Path
from pkg_resources import resource_filename, resource_string as resource_bytes


def latexmkrc_as_string():
    """Return the content of `latexmkrc` as a string."""
    # importlib.resources.read_text would be better, but I don't feel like adding
    # a dependency.  pkg_resources does a bunch of weird stuff.  Instead, I've just
    # set zip_safe=False so this is always a real file.
    return (Path(__file__).parent/'latexmkrc').open().read()


def latexmkrc_with_dependencies():
    """Return `latexmkrc` with dependencies on the files in this package added."""
    # Again, importlib.resources.contents would be better.
    dep_files = [p for p in sorted(Path(__file__).parent.iterdir()) if p.is_file()]
    dep_commands = ['    rdb_ensure_file($rule, "%s");' % f for f in dep_files]
    return latexmkrc_as_string().replace(
        '    ### <depend on pythontexfigures package>',
        '    # Depend on pythontexfigures package files\n' + '\n'.join(dep_commands)
    )

if __name__ == '__main__':
    print(latexmkrc_with_dependencies())
