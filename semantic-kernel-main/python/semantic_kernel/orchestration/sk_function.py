# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import platform
import sys
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.delegate_handlers import DelegateHandlers
from semantic_kernel.orchestration.delegate_inference import DelegateInference
from semantic_kernel.orchestration.delegate_types import DelegateTypes
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.skill_definition.function_view import FunctionView
from semantic_kernel.skill_definition.parameter_view import ParameterView
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext

if platform.system() == "Windows" and sys.version_info >= (3, 8, 0):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logger: logging.Logger = logging.getLogger(__name__)


class SKFunction(SKFunctionBase):
    """
    Semantic Kernel function.
    """

    # TODO: rebuild with proper pydantic fields
    _parameters: List[ParameterView]
    _delegate_type: DelegateTypes
    _function: Callable[..., Any]
    _skill_collection: Optional[ReadOnlySkillCollectionBase]
    _ai_service: Optional[Union[TextCompletionClientBase, ChatCompletionClientBase]]
    _ai_request_settings: AIRequestSettings
    _chat_prompt_template: ChatPromptTemplate

    @staticmethod
    def from_native_method(method, skill_name="", log=None) -> "SKFunction":
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        if method is None:
            raise ValueError("Method cannot be `None`")

        assert method.__sk_function__ is not None, "Method is not a SK function"
        assert method.__sk_function_name__ is not None, "Method name is empty"

        parameters = []
        # sk_function_context_parameters are optionals
        if hasattr(method, "__sk_function_context_parameters__"):
            for param in method.__sk_function_context_parameters__:
                assert "name" in param, "Parameter name is empty"
                assert "description" in param, "Parameter description is empty"
                assert "default_value" in param, "Parameter default value is empty"

                parameters.append(
                    ParameterView(
                        name=param["name"],
                        description=param["description"],
                        default_value=param["default_value"],
                        type=param.get("type", "string"),
                        required=param.get("required", False),
                    )
                )

        if (
            hasattr(method, "__sk_function_input_description__")
            and method.__sk_function_input_description__ is not None
            and method.__sk_function_input_description__ != ""
        ):
            input_param = ParameterView(
                name="input",
                description=method.__sk_function_input_description__,
                default_value=method.__sk_function_input_default_value__,
                type="string",
                required=False,
            )
            parameters = [input_param] + parameters

        return SKFunction(
            delegate_type=DelegateInference.infer_delegate_type(method),
            delegate_function=method,
            delegate_stream_function=method,
            parameters=parameters,
            description=method.__sk_function_description__,
            skill_name=skill_name,
            function_name=method.__sk_function_name__,
            is_semantic=False,
        )

    @staticmethod
    def from_semantic_config(
        skill_name: str,
        function_name: str,
        function_config: SemanticFunctionConfig,
        log: Optional[Any] = None,
    ) -> "SKFunction":
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        if function_config is None:
            raise ValueError("Function configuration cannot be `None`")

        async def _local_func(client, request_settings, context: "SKContext", **kwargs):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if not function_config.has_chat_prompt:
                    prompt = await function_config.prompt_template.render_async(context)
                    completion = await client.complete_async(prompt, request_settings)
                    context.variables.update(completion)
                    return context
            except Exception as e:
                # TODO: "critical exceptions"
                context.fail(str(e), e)
                return context

            as_chat_prompt = function_config.prompt_template
            # Similar to non-chat, render prompt (which renders to a
            # dict of <role, content, name> messages)
            messages = await as_chat_prompt.render_messages_async(context)
            try:
                result = await client.complete_chat_async(messages, request_settings)
                if isinstance(result, list):
                    # TODO: handle multiple completions
                    result = result[0]
                if isinstance(result, tuple):
                    completion, tool_message, function_call = result
                else:
                    completion = result
                    tool_message = None
                    function_call = None
                if tool_message:
                    context.objects["tool_message"] = tool_message
                    as_chat_prompt.add_message(role="tool", message=tool_message)
                as_chat_prompt.add_message("assistant", message=completion, function_call=function_call)
                if completion is not None:
                    context.variables.update(completion)
                if function_call is not None:
                    context.objects["function_call"] = function_call
            except Exception as exc:
                # TODO: "critical exceptions"
                context.fail(str(exc), exc)
            finally:
                return context

        async def _local_stream_func(client, request_settings, context):
            if client is None:
                raise ValueError("AI LLM service cannot be `None`")

            try:
                if function_config.has_chat_prompt:
                    chat_prompt = function_config.prompt_template

                    # Similar to non-chat, render prompt (which renders to a
                    # list of <role, content> messages)
                    completion = ""
                    messages = await chat_prompt.render_messages_async(context)
                    async for partial_content in client.complete_chat_stream_async(
                        messages=messages, settings=request_settings
                    ):
                        if isinstance(partial_content, str):
                            completion += partial_content
                            yield partial_content
                        else:
                            tool_message = await partial_content.get_tool_message()
                            if tool_message:
                                chat_prompt.add_message(role="tool", message=tool_message)
                                context.objects["tool_message"] = tool_message
                            # Get the completion
                            async for part in partial_content:
                                completion += part
                                yield part
                    # Use the full completion to update the chat_prompt_template and context
                    chat_prompt.add_assistant_message(completion)
                    context.variables.update(completion)
                else:
                    prompt = await function_config.prompt_template.render_async(context)

                    completion = ""
                    async for partial_content in client.complete_stream_async(prompt, request_settings):
                        completion += partial_content
                        yield partial_content
                    context.variables.update(completion)
            except Exception as e:
                # TODO: "critical exceptions"
                context.fail(str(e), e)

        return SKFunction(
            delegate_type=DelegateTypes.ContextSwitchInSKContextOutTaskSKContext,
            delegate_function=_local_func,
            delegate_stream_function=_local_stream_func,
            parameters=function_config.prompt_template.get_parameters(),
            description=function_config.prompt_template_config.description,
            skill_name=skill_name,
            function_name=function_name,
            is_semantic=True,
            chat_prompt_template=function_config.prompt_template if function_config.has_chat_prompt else None,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def skill_name(self) -> str:
        return self._skill_name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> List[ParameterView]:
        return self._parameters

    @property
    def is_semantic(self) -> bool:
        return self._is_semantic

    @property
    def is_native(self) -> bool:
        return not self._is_semantic

    @property
    def request_settings(self) -> AIRequestSettings:
        return self._ai_request_settings

    def __init__(
        self,
        delegate_type: DelegateTypes,
        delegate_function: Callable[..., Any],
        parameters: List[ParameterView],
        description: str,
        skill_name: str,
        function_name: str,
        is_semantic: bool,
        log: Optional[Any] = None,
        delegate_stream_function: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__()
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        self._delegate_type = delegate_type
        self._function = delegate_function
        self._parameters = parameters
        self._description = description
        self._skill_name = skill_name
        self._name = function_name
        self._is_semantic = is_semantic
        self._stream_function = delegate_stream_function
        self._skill_collection = None
        self._ai_service = None
        self._ai_request_settings = AIRequestSettings()
        self._chat_prompt_template = kwargs.get("chat_prompt_template", None)

    def set_default_skill_collection(self, skills: ReadOnlySkillCollectionBase) -> "SKFunction":
        self._skill_collection = skills
        return self

    def set_ai_service(self, ai_service: Callable[[], TextCompletionClientBase]) -> "SKFunction":
        if ai_service is None:
            raise ValueError("AI LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self._ai_service = ai_service()
        return self

    def set_chat_service(self, chat_service: Callable[[], ChatCompletionClientBase]) -> "SKFunction":
        if chat_service is None:
            raise ValueError("Chat LLM service factory cannot be `None`")
        self._verify_is_semantic()
        self._ai_service = chat_service()
        return self

    def set_ai_configuration(self, settings: AIRequestSettings) -> "SKFunction":
        if settings is None:
            raise ValueError("AI LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self._ai_request_settings = settings
        return self

    def set_chat_configuration(self, settings: AIRequestSettings) -> "SKFunction":
        if settings is None:
            raise ValueError("Chat LLM request settings cannot be `None`")
        self._verify_is_semantic()
        self._ai_request_settings = settings
        return self

    def describe(self) -> FunctionView:
        return FunctionView(
            name=self.name,
            skill_name=self.skill_name,
            description=self.description,
            is_semantic=self.is_semantic,
            parameters=self._parameters,
        )

    def __call__(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[AIRequestSettings] = None,
        log: Optional[Any] = None,
    ) -> "SKContext":
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        return self.invoke(
            input=input,
            variables=variables,
            context=context,
            memory=memory,
            settings=settings,
        )

    def invoke(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[AIRequestSettings] = None,
        log: Optional[Any] = None,
    ) -> "SKContext":
        from semantic_kernel.orchestration.sk_context import SKContext

        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
            if memory is not None:
                context.memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            loop = asyncio.get_running_loop() if asyncio.get_event_loop().is_running() else None
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            coroutine_function = self._invoke_semantic_async if self.is_semantic else self._invoke_native_async
            return self.run_async_in_executor(lambda: coroutine_function(context, settings))
        else:
            if self.is_semantic:
                return asyncio.run(self._invoke_semantic_async(context, settings))
            else:
                return asyncio.run(self._invoke_native_async(context))

    async def invoke_async(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[AIRequestSettings] = None,
        **kwargs: Dict[str, Any],
    ) -> "SKContext":
        from semantic_kernel.orchestration.sk_context import SKContext

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
            if memory is not None:
                context.memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                return await self._invoke_semantic_async(context, settings, **kwargs)
            else:
                return await self._invoke_native_async(context, **kwargs)
        except Exception as e:
            context.fail(str(e), e)
            return context

    async def _invoke_semantic_async(self, context: "SKContext", settings: AIRequestSettings, **kwargs):
        self._verify_is_semantic()
        self._ensure_context_has_skills(context)
        new_context = await self._function(self._ai_service, settings or self._ai_request_settings, context)
        context.variables.merge_or_overwrite(new_context.variables)
        return context

    async def _invoke_native_async(self, context):
        self._verify_is_native()

        self._ensure_context_has_skills(context)

        delegate = DelegateHandlers.get_handler(self._delegate_type)
        # for python3.9 compatibility (staticmethod is not callable)
        if not hasattr(delegate, "__call__"):
            delegate = delegate.__func__
        new_context = await delegate(self._function, context)

        return new_context

    def _verify_is_semantic(self) -> None:
        if self._is_semantic:
            return

        logger.error("The function is not semantic")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a semantic function",
        )

    def _verify_is_native(self) -> None:
        if not self._is_semantic:
            return

        logger.error("The function is not native")
        raise KernelException(
            KernelException.ErrorCodes.InvalidFunctionType,
            "Invalid operation, the method requires a native function",
        )

    async def invoke_stream_async(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[AIRequestSettings] = None,
    ):
        from semantic_kernel.orchestration.sk_context import SKContext

        if context is None:
            context = SKContext(
                variables=ContextVariables("") if variables is None else variables,
                skill_collection=self._skill_collection,
                memory=memory if memory is not None else NullMemory.instance,
            )
        else:
            # If context is passed, we need to merge the variables
            if variables is not None:
                context.variables = variables.merge_or_overwrite(new_vars=context.variables, overwrite=False)
            if memory is not None:
                context._memory = memory

        if input is not None:
            context.variables.update(input)

        try:
            if self.is_semantic:
                async for stream_msg in self._invoke_semantic_stream_async(context, settings):
                    yield stream_msg
            else:
                async for stream_msg in self._invoke_native_stream_async(context):
                    yield stream_msg
        except Exception as e:
            context.fail(str(e), e)
            raise KernelException(
                KernelException.ErrorCodes.FunctionInvokeError,
                "Error occurred while invoking stream function",
            )

    async def _invoke_semantic_stream_async(self, context, settings):
        self._verify_is_semantic()
        self._ensure_context_has_skills(context)
        async for stream_msg in self._stream_function(self._ai_service, settings or self._ai_request_settings, context):
            yield stream_msg

    async def _invoke_native_stream_async(self, context):
        self._verify_is_native()

        self._ensure_context_has_skills(context)

        delegate = DelegateHandlers.get_handler(self._delegate_type)
        # for python3.9 compatibility (staticmethod is not callable)
        if not hasattr(delegate, "__call__"):
            delegate = delegate.__func__

        completion = ""
        async for partial in delegate(self._function, context):
            completion += partial
            yield partial

        context.variables.update(completion)

    def _ensure_context_has_skills(self, context) -> None:
        if context.skills is not None:
            return

        context.skills = self._skill_collection

    def _trace_function_type_Call(self, type: Enum) -> None:
        logger.debug(f"Executing function type {type}: {type.name}")

    """
    Async code wrapper to allow running async code inside external
    event loops such as Jupyter notebooks.
    """

    def run_async_in_executor(self, coroutine_func: Callable[[], Any]) -> Any:
        """
        A unified method for async execution for more efficient and safer thread management

        Arguments:
            coroutine_func {Callable[[], Any]} -- The coroutine to run

        Returns:
            Any -- The result of the coroutine
        """

        def run_async_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(coroutine_func())
            loop.close()
            return result

        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_async_in_thread)
            return future.result()
