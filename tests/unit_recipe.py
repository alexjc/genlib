# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

import pytest

from genlib.recipe import Recipe
from genlib.schema import SkillSchema, SkillInput, SkillOutput


@pytest.fixture
def fake_schema():
    return SkillSchema(uri="fake", inputs=[SkillInput("A", spec="int")], outputs=[])


class TestRecipe:
    def test_construct(self, fake_schema):
        recipe = Recipe(fake_schema, {"A": 0})
        assert len(recipe.parameters) == 1

    def test_unspecified(self, fake_schema):
        recipe = Recipe(fake_schema, {})
        assert len(recipe.parameters) == 0
        assert recipe.is_unspecified("A")
