# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import unittest
import itertools

import pytest

from genlib.types import check_type


ATOMIC_TYPES = ("float", "int", "str", "bool", "Any", "T")


class TestAtomicTypes(unittest.TestCase):
    def test_define_valid(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"{t}") is True

    def test_define_invalid(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"{t[:-1]}") is False


class TestCompositeTypes(unittest.TestCase):
    def test_define_list_specific(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"List[{t}]") is True
            assert check_type(f"List({t})") is False

    def test_define_list_invalid(self):
        assert check_type("List(Nope)") is False
        assert check_type("List[Nope]") is False

    def test_define_dict_valid(self):
        for t1, t2 in itertools.product(ATOMIC_TYPES, repeat=2):
            assert check_type(f"Dict[{t1}, {t2}]") is True

    def test_define_dict_two_arguments_unknown(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"Dict[Nope, {t}]") is False
            assert check_type(f"Dict[{t}, Nope]") is False

    def test_define_dict_one_argument_known(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"Dict({t})") is False
            assert check_type(f"Dict[{t}]") is False

    def test_define_dict_one_argument_unknown(self):
        assert check_type("Dict(Nope)") is False
        assert check_type("Dict[Nope]") is False
