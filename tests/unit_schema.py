# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import unittest

import pytest

from genlib.schema import Input, Output


class TestInputDefinitions(unittest.TestCase):
    def test_input_minimal(self):
        i = Input("test", spec="int")
        assert i

    def test_input_full(self):
        i = Input("full", spec="str", defaults=["A", "B"], desc="This is a test.")
        assert i


class TestOutputDefinitions(unittest.TestCase):
    def test_output_minimal(self):
        o = Output("test", spec="int")
        assert o

    def test_output_full(self):
        o = Output("full", spec="str", desc="This is a test too.")
        assert o
