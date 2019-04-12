# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import sys


def pytest():
    """Entry point for pytest as Poetry command with manually-specified arguments.
    """
    from pytest import main

    sys.exit(main(["-c", "tests/pytest.ini"] + sys.argv[1:]))


def pylint():
    """Entry point for pytest as Poetry command with manually-specified arguments.
    """
    from pylint.lint import Run as main

    sys.exit(main(["genlib", "--rcfile", "tests/pylint.ini"] + sys.argv[1:]))
