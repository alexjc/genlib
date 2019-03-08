# genlib — Copyright (c) 2019, Alex J. Champandard. Code licensed under the GNU AGPLv3.

from genlib.schema import SkillSchema, SkillInput, SkillOutput


class TestInputDefinitions:
    def test_input_minimal(self):
        i = SkillInput("test", spec="int")
        assert i

    def test_input_full_dict(self):
        i = SkillInput("full", spec="str", defaults=["A", "B"], desc="This is a test.")
        data = i.as_dict()
        assert len(data) == 4
        assert set(data.keys()) == {"name", "spec", "defaults", "desc"}


class TestOutputDefinitions:
    def test_output_minimal(self):
        o = SkillOutput("test", spec="int")
        assert o

    def test_output_full_dict(self):
        o = SkillOutput("full", spec="str", desc="This is a test too.")
        data = o.as_dict()
        assert len(data) == 3
        assert set(data.keys()) == {"name", "spec", "desc"}


class TestSchemaDefinition:
    def test_schema_as_dict(self):
        schema = SkillSchema(
            "test.py:Example",
            inputs=[SkillInput("test", spec="int")],
            outputs=[SkillOutput("test", spec="int")],
        )
        data = schema.as_dict()
        assert len(data) == 3
        assert len(data["inputs"]) == 1
        assert len(data["outputs"]) == 1
        assert data["uri"] == "test.py:Example"
