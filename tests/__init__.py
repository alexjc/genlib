# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest


def main():
    """Entry point for Poetry run command-line with manually-specified arguments.
    """
    pytest.main(["-c", "tests/pytest.ini"])
