"""Integration test for example documents.

Author: Matthew Edwards
Date: July 2019
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
from typing import Union


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
        pdf_filename (Union[str, Path]): Filename of PDF to convert.
        output_pattern (Union[str, Path]): Filename pattern for output images, with %d for page
            number.
    """
    subprocess.check_call([
        'convert', '-density', '300', str(pdf_filename), str(output_pattern)
    ])


def image_difference(a, b):
    """Get the RMS pixel difference between two images using ImageMagick.

    See https://www.imagemagick.org/Usage/compare/
    Args:
        a (Union[str, Path]): Filename of first image.
        b (Union[str, Path]): Filename of second image.
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


def assert_results_match_example(expected_path, test_dir):
    """Compare expected PDF with test results.

    Args:
        expected_path (Union[str, Path]): Path to expected PDF in examples folder.
        test_dir (Union[str, Path]): Path to test output folder.
    """
    output_path = test_dir/expected_path.name
    if files_identical(expected_path, output_path):
        print('Output is binary identical')
        return

    print('Comparing visually')
    pdf_to_images(expected_path, test_dir/'expected-%d.png')
    pdf_to_images(output_path, test_dir/'actual-%d.png')
    expected_pages = len(list(test_dir.glob('expected-*')))
    assert len(list(test_dir.glob('actual-*'))) == expected_pages
    for i in range(expected_pages):
        expected_page = test_dir/f'expected-{i}.png'
        actual_page = test_dir/f'actual-{i}.png'
        assert image_difference(expected_page, actual_page) == 0


def save_output_files(test_dir, test_name):
    """Copy output files from failed test into main folder."""
    out_dir = Path(__file__).parent/'output'/test_name  # type: Path
    out_dir.mkdir(parents=True, exist_ok=True)
    print('Copying results to', out_dir)
    for f in test_dir.glob('*.pdf'):
        shutil.copy(f, out_dir)
    for f in test_dir.glob('*.png'):
        shutil.copy(f, out_dir)


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

    # Check output matches example
    try:
        assert_results_match_example(example_dir/'example.pdf', tmp_dir)
    except (subprocess.CalledProcessError, AssertionError):
        save_output_files(tmp_dir, test_name="basic")
        raise


def copy_subfiles_files(tmpdir):
    """Copy files for subfiles example document into temp dir."""
    project_dir = Path(__file__).resolve().parent.parent  # type: Path
    example_dir = project_dir/'examples'/'subfiles'
    tmp_dir = Path(tmpdir)
    (tmp_dir/'sections'/'section1'/'scripts').mkdir(parents=True)
    (tmp_dir/'sections'/'section2').mkdir(parents=True)
    for name in [
        'latexmkrc', 'example-with-subfiles.tex', 'sections/section1/section1.tex',
        'sections/section1/scripts/polynomial.py','sections/section2/section2.tex'
    ]:
        shutil.copy(example_dir/name, tmp_dir/name)
    print('Temp dir contents:')
    for f in tmp_dir.iterdir():
        print(f.relative_to(tmp_dir))
    return example_dir


def test_building_subfiles_example(tmpdir):
    """Build the subfiles example document and check the output is identical."""
    tmp_dir = Path(tmpdir)
    example_dir = copy_subfiles_files(tmp_dir)

    # Run latexmk
    subprocess.check_call('latexmk example-with-subfiles.tex'.split(' '), cwd=tmp_dir)

    # Check output matches example
    try:
        assert_results_match_example(example_dir/'example-with-subfiles.pdf', tmp_dir)
    except (subprocess.CalledProcessError, AssertionError):
        save_output_files(tmp_dir, test_name="subfiles")
        raise


def test_building_subfiles_example_section1(tmpdir):
    """Build section 1 of the  subfiles example document and check the output is
    identical."""
    tmp_dir = Path(tmpdir)
    example_dir = copy_subfiles_files(tmp_dir)

    # Run latexmk
    subprocess.check_call('latexmk sections/section1/section1.tex'.split(' '), cwd=tmp_dir)

    # Check output matches example
    try:
        assert_results_match_example(example_dir/'section1.pdf', tmp_dir)
    except (subprocess.CalledProcessError, AssertionError):
        save_output_files(tmp_dir, test_name="subfiles-section1")
        raise


def test_building_subfiles_example_section2(tmpdir):
    """Build section 2 of the  subfiles example document and check the output is
    identical."""
    tmp_dir = Path(tmpdir)
    example_dir = copy_subfiles_files(tmp_dir)

    # Run latexmk
    subprocess.check_call('latexmk sections/section2/section2.tex'.split(' '), cwd=tmp_dir)

    # Check output matches example
    try:
        assert_results_match_example(example_dir/'section2.pdf', tmp_dir)
    except (subprocess.CalledProcessError, AssertionError):
        save_output_files(tmp_dir, test_name="subfiles-section2")
        raise
