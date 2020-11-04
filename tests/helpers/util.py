"""Utility functions for tests."""
import subprocess


def build(filename: str):
    """Use pdflatex and pythontex to build the given tex document."""
    pdflatex = ["pdflatex", "-interaction=nonstopmode", filename]
    pythontex = ["pythontex", filename]

    result = subprocess.run(pdflatex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "First pdflatex run failed: " + result.stdout
    result = subprocess.run(pythontex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "pythontex failed: " + result.stdout
    result = subprocess.run(pdflatex, capture_output=True, encoding="utf8")
    assert result.returncode == 0, "Second pdflatex run failed: " + result.stdout
