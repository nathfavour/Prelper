# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING

from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.skill_definition.sk_function_decorator import sk_function

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


def test_init_native_function_with_input_description():
    def mock_function(input: str, context: "SKContext") -> None:
        pass

    mock_function.__sk_function__ = True
    mock_function.__sk_function_name__ = "mock_function"
    mock_function.__sk_function_description__ = "Mock description"
    mock_function.__sk_function_input_description__ = "Mock input description"
    mock_function.__sk_function_input_default_value__ = "default_input_value"
    mock_function.__sk_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
        }
    ]

    mock_method = mock_function

    native_function = SKFunction.from_native_method(mock_method, "MockSkill")

    assert native_function._function == mock_method
    assert native_function._parameters[0].name == "input"
    assert native_function._parameters[0].description == "Mock input description"
    assert native_function._parameters[0].default_value == "default_input_value"
    assert native_function._parameters[0].type_ == "string"
    assert native_function._parameters[0].required is False
    assert native_function._parameters[1].name == "param1"
    assert native_function._parameters[1].description == "Param 1 description"
    assert native_function._parameters[1].default_value == "default_param1_value"
    assert native_function._parameters[1].type_ == "string"
    assert native_function._parameters[1].required is False


def test_init_native_function_without_input_description():
    def mock_function(context: "SKContext") -> None:
        pass

    mock_function.__sk_function__ = True
    mock_function.__sk_function_name__ = "mock_function_no_input_desc"
    mock_function.__sk_function_description__ = "Mock description no input desc"
    mock_function.__sk_function_context_parameters__ = [
        {
            "name": "param1",
            "description": "Param 1 description",
            "default_value": "default_param1_value",
            "required": True,
        }
    ]

    mock_method = mock_function

    native_function = SKFunction.from_native_method(mock_method, "MockSkill")

    assert native_function._function == mock_method
    assert native_function._parameters[0].name == "param1"
    assert native_function._parameters[0].description == "Param 1 description"
    assert native_function._parameters[0].default_value == "default_param1_value"
    assert native_function._parameters[0].type_ == "string"
    assert native_function._parameters[0].required is True


def test_init_native_function_from_sk_function_decorator():
    @sk_function(
        description="Test description",
        name="test_function",
        input_description="Test input description",
        input_default_value="test_default_value",
    )
    def decorated_function() -> None:
        pass

    assert decorated_function.__sk_function__ is True
    assert decorated_function.__sk_function_description__ == "Test description"
    assert decorated_function.__sk_function_name__ == "test_function"
    assert decorated_function.__sk_function_input_description__ == "Test input description"
    assert decorated_function.__sk_function_input_default_value__ == "test_default_value"

    native_function = SKFunction.from_native_method(decorated_function, "MockSkill")

    assert native_function._function == decorated_function
    assert native_function._parameters[0].name == "input"
    assert native_function._parameters[0].description == "Test input description"
    assert native_function._parameters[0].default_value == "test_default_value"
    assert native_function._parameters[0].type_ == "string"
    assert native_function._parameters[0].required is False


def test_init_native_function_from_sk_function_decorator_defaults():
    @sk_function()
    def decorated_function() -> None:
        pass

    assert decorated_function.__sk_function__ is True
    assert decorated_function.__sk_function_description__ == ""
    assert decorated_function.__sk_function_name__ == "decorated_function"
    assert decorated_function.__sk_function_input_description__ == ""
    assert decorated_function.__sk_function_input_default_value__ == ""

    native_function = SKFunction.from_native_method(decorated_function, "MockSkill")

    assert native_function._function == decorated_function
    assert len(native_function._parameters) == 0
