"""Installer for pythontexfigures.sty.

Author: Matthew Edwards
Date: July 2019
"""

from pathlib import Path
import subprocess
import sys

from .sty import sty_file_as_string


def install(tree='TEXMFLOCAL'):
    texmf_path = subprocess.check_output(['kpsewhich', '-var-value=' + tree])
    texmf_path = texmf_path.decode('utf8').strip()
    path = Path(texmf_path)/'tex'/'latex'/'pythontexfigures'
    path.mkdir(parents=True, exist_ok=True)
    print('Installing pythontexfigures.sty into', path)
    (path/'pythontexfigures.sty').open('w').write(sty_file_as_string())
    subprocess.check_call('mktexlsr')


if __name__ == '__main__':
    # TODO: Not lazy
    try:
        if len(sys.argv) > 1:
            install(sys.argv[1])
        else:
            install()
    except Exception as e:
        print(e)
        print('Usage: python3 -m pythontexfigures.install TEXMFLOCAL|TEXMFHOME')
