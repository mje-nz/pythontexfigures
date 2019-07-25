"""Integration test for example documents.

Author: Matthew Edwards
Date: July 2019
"""
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


def files_identical(a, b):
    """Return whether two files are bit-for-bit identical."""
    if os.path.getsize(a) != os.path.getsize(b):
        # Don't bother hashing them if they aren't even the same size
        return False
    return hash_file(a) == hash_file(b)


def pdf_to_images(pdf_filename, output_pattern):
    """Convert a PDF to a series of images (of each page) using ImageMagick.

    Args:
        pdf_filename (str): Filename of PDF to convert.
        outut_pattern (str): Filename pattern for output images, with %d for page
            number.
    """
    subprocess.check_call([
        'convert', '-density', '300', str(pdf_filename), str(output_pattern)
    ])


def image_difference(a, b):
    """Get the RMS pixel difference between two images using ImageMagick.

    See https://www.imagemagick.org/Usage/compare/
    Args:
        a (str): Filename of first image.
        b (str): Filename of second image.
    Returns:
        float: RMS pixel error (0-1).
    """
    exit_code, output = subprocess.getstatusoutput(
        f'compare -metric RMSE {str(a)} {str(b)} null:'
    )
    if exit_code > 1:
        raise subprocess.CalledProcessError(output)
    absolute, normalised = output.split(' ')
    assert normalised.startswith('(')
    assert normalised.endswith(')')
    return float(normalised[1:-1])


def test_building_basic_example(tmpdir):
    """Build the basic example document and check the output is identical."""
    # Copy files into temp dir
    project_dir = Path(__file__).resolve().parent.parent  # type: Path
    example_dir = project_dir/'examples'/'basic'
    tmp_dir = Path(tmpdir)
    os.mkdir(tmp_dir/'scripts')
    for name in ['latexmkrc', 'example.tex', 'scripts/test.py']:
        shutil.copy(example_dir/name, tmp_dir/name)
    print('Temp dir contents:')
    for f in tmp_dir.iterdir():
        print(f.relative_to(tmp_dir))

    # Run latexmk
    subprocess.check_call('latexmk example.tex'.split(' '), cwd=tmp_dir)

    # Check output is identical
    if files_identical(example_dir/'example.pdf', tmp_dir/'example.pdf'):
        print('Output is binary identical')
        return
    try:
        pdf_to_images(example_dir/'example.pdf', tmp_dir/'expected-%d.png')
        pdf_to_images(tmp_dir/'example.pdf', tmp_dir/'actual-%d.png')
        assert len(list(tmp_dir.glob('expected-*'))) == 2
        assert len(list(tmp_dir.glob('actual-*'))) == 2
        assert image_difference(tmp_dir/'expected-0.png', tmp_dir/'actual-0.png') == 0
        assert image_difference(tmp_dir/'expected-1.png', tmp_dir/'actual-1.png') == 0
    except (subprocess.CalledProcessError, AssertionError):
        out_dir = project_dir/'tests'/'output'  # type: Path
        out_dir.mkdir(exist_ok=True)
        shutil.copy(example_dir/'example.pdf', out_dir)
        for f in tmp_dir.glob('*.png'):
            shutil.copy(f, out_dir)
        raise

