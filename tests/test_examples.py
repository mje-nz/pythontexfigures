"""Integration test for example documents.

Author: Matthew Edwards
Date: July 2019
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import _pytest.fixtures  # noqa: I900
import pytest

from pythontexfigures.util import StrPath


def hash_file(filename: StrPath):
    """Return the SHA1 hash of the given file."""
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()
    with open(filename, "rb") as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def files_identical(a: StrPath, b: StrPath):
    """Return whether two files are bit-for-bit identical."""
    if os.path.getsize(a) != os.path.getsize(b):
        # Don't bother hashing them if they aren't even the same size
        return False
    return hash_file(a) == hash_file(b)


def pdf_to_images(pdf_filename: StrPath, output_pattern: StrPath):
    """Convert a PDF to a series of images (of each page) using ImageMagick.

    Args:
        pdf_filename: Filename of PDF to convert.
        output_pattern: Filename pattern for output images, with %d for page
            number.
    """
    subprocess.check_call(
        ["convert", "-density", "300", str(pdf_filename), str(output_pattern)]
    )


def image_difference(a: StrPath, b: StrPath):
    """Get the RMS pixel difference between two images using ImageMagick.

    See https://www.imagemagick.org/Usage/compare/

    Returns:
        RMS pixel error (0-1).
    """
    cmd = f"compare -metric RMSE {a} {b} null:"
    exit_code, output = subprocess.getstatusoutput(cmd)
    # compare returns 1 if the images are different at all
    if exit_code > 1:
        raise subprocess.CalledProcessError(exit_code, cmd)
    absolute, normalised = output.split(" ")
    assert normalised.startswith("(")
    assert normalised.endswith(")")
    return float(normalised[1:-1])


def assert_results_match_example(expected_path: StrPath, test_dir: StrPath):
    """Compare expected PDF with test results.

    Args:
        expected_path: Path to expected PDF in examples folder.
        test_dir: Path to test output folder.
    """
    expected_path = Path(expected_path)
    test_dir = Path(test_dir)
    output_path = test_dir / expected_path.name
    if files_identical(expected_path, output_path):
        print("Output is binary identical")
        return

    print("Comparing visually")
    pdf_to_images(expected_path, test_dir / "expected-%d.png")
    pdf_to_images(output_path, test_dir / "actual-%d.png")
    expected_pages = len(list(test_dir.glob("expected-*")))
    assert len(list(test_dir.glob("actual-*"))) == expected_pages
    for i in range(expected_pages):
        expected_page = test_dir / f"expected-{i}.png"
        actual_page = test_dir / f"actual-{i}.png"
        assert image_difference(expected_page, actual_page) == 0


@pytest.fixture
def save_output_files_on_failure(request: _pytest.fixtures.FixtureRequest):
    """Copy output files from failed tests into main folder."""
    yield
    if request.node.result_call.passed:
        return

    test_dir = Path()
    out_dir = Path(__file__).parent / "output" / request.node.name.replace("/", "-")
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Copying results to", out_dir)
    for f in test_dir.glob("*.pdf"):
        shutil.copy(f, out_dir)
    for f in test_dir.glob("*.png"):
        shutil.copy(f, out_dir)


def tree(root_dir: StrPath = "."):
    """Print the files in the given directory and its subdirectories."""
    for f in sorted(Path(root_dir).rglob("*")):
        if f.is_file():
            print(f)


@pytest.mark.parametrize(
    "tex_file",
    (
        "basic/example.tex",
        "subfiles/example-with-subfiles.tex",
        "subfiles/sections/section1/section1.tex",
        "subfiles/sections/section2/section2.tex",
    ),
)
def test_building_examples(tex_file, in_temp_dir, save_output_files_on_failure):
    """Build each example document and check the output is identical."""
    # Find example root dir
    tex_file = Path(tex_file)
    project_dir = Path(__file__).parent.parent
    example_dir = project_dir / "examples" / tex_file.parts[0]
    tex_file = tex_file.relative_to(tex_file.parts[0])

    # Copy files into temp dir
    for pattern in ("latexmkrc", "*.tex", "scripts/*.py"):
        for filename in example_dir.rglob(pattern):
            filename = filename.relative_to(example_dir)
            filename.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(example_dir / filename, filename)
    print("Temp dir contents:")
    tree()

    # Build and check output matches
    subprocess.check_call(["latexmk", str(tex_file)])
    output_filename = tex_file.stem + ".pdf"
    assert_results_match_example(example_dir / output_filename, ".")
