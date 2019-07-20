"""Installer for pythontexfigures.sty.

Author: Matthew Edwards
Date: July 2019
"""

from pathlib import Path
import subprocess
import sys

from .sty import sty_file_as_string


def install(tree):
    exit_code, texmf_path = subprocess.getstatusoutput('kpsewhich -var-value=' + tree)
    if exit_code != 0:
        raise ValueError('Could not get path for ' + tree)
    path = Path(texmf_path)/'tex'/'latex'/'pythontexfigures'
    path.mkdir(parents=True)
    print('Installing pythontexfigures.sty into', path)
    (path/'pythontexfigures.sty').open('w').write(sty_file_as_string())


if __name__ == '__main__':
    try:
        install(sys.argv[1])
    except Exception as e:
        print(e)
        print('Usage: python3 -m pythontexfigures.install TEXMFLOCAL|TEXMFHOME')
