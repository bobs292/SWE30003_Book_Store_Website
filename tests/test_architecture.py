import subprocess
import sys

# ============================================================================
# Architecture tests
# These tests enforce the layered architecture dependency rule by running
# import-linter as part of the test suite. import-linter reads the contracts
# defined in pyproject.toml and checks that no file in any layer imports
# from a layer above it.
#
# The four contracts checked are:
#   - Presentation cannot import from data
#   - Domain cannot import from data
#   - Domain cannot import from presentation
#   - Data cannot import from presentation
#
# If any of these fail it means a file has crossed a layer boundary in the
# wrong direction. The test output will show exactly which file and which
# import caused the violation.


def test_import_contracts_are_all_kept():
    # Runs lint-imports using the same Python interpreter that pytest is
    # using. subprocess.run executes it as a separate process and captures
    # the output. We check the return code: 0 means all contracts passed,
    # anything else means at least one contract was broken.
    result = subprocess.run(
        ['lint-imports'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        "One or more import contracts are broken.\n\n"
        + result.stdout
        + result.stderr
    )
