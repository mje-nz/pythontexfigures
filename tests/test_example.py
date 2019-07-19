import hashlib
import os
from pathlib import Path
import shutil
import subprocess


def hash_file(filename):
    """Return the SHA1 hash of the given file."""
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def test_building_example(tmpdir):
    """Build the example file and check the output is identical."""
    # Copy files into temp dir
    project_dir = Path(__file__).resolve().parent.parent
    example_dir = project_dir/'example'
    tmp_dir = Path(tmpdir)
    os.mkdir(tmp_dir/'scripts')
    for name in ['latexmkrc', 'example.tex', 'scripts/test.py']:
        shutil.copy(example_dir/name, tmp_dir/name)
    print('Temp dir contents:')
    for f in tmp_dir.iterdir():
        print(f.relative_to(tmp_dir))
    os.chdir(tmp_dir)

    # Run latexmk
    subprocess.check_call('latexmk example.tex'.split(' '))

    # Check output is identical
    assert hash_file(example_dir/'example.pdf') == hash_file(tmp_dir/'example.pdf')
