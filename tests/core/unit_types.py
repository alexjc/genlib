# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import typing
import itertools

from genlib.core.types import check_type, add_type_class


ATOMIC_TYPES = ("float", "int", "str", "bool", "Any", "T")


class TestAtomicTypes:
    def test_define_valid(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"{t}") is True

    def test_define_invalid(self):
        for t in ATOMIC_TYPES:
            assert check_type(f"{t[:-1]}") is False


class TestCompositeTypes:
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


class TestCustomTypes:
    def test_add_type_class(self):
        custom_type = typing.NewType("Custom", object)
        add_type_class("Custom", custom_type)

    def test_use_custom_type(self):
        binary_type = typing.NewType("Binary", typing.ByteString)
        add_type_class("Binary", binary_type)
        assert check_type("Binary") is True
