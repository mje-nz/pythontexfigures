"""pytest configuration file."""
import sys
from pathlib import Path

import _pytest.reports  # noqa: I900
import pytest

# Add helpers folder to path
sys.path.append(str(Path(__file__) / "helpers"))


@pytest.fixture
def in_temp_dir(tmpdir):
    """Create a temporary directory and change to it for the duration of the test."""
    with tmpdir.as_cwd():
        yield Path(str(tmpdir))


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call):
    """Make test result information available in fixtures.

    From https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures  # noqa: B950
    """
    # Execute all other hooks to obtain the result object
    outcome = yield  # type: _pytest.reports.TestReport
    result = outcome.get_result()

    # Save the result for test phase ("setup", "call", or "teardown")
    setattr(item, "result_" + result.when, result)
