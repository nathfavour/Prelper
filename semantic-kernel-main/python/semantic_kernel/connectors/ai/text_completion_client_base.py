# Copyright (c) Microsoft. All rights reserved.


from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, AsyncGenerator, List, Optional, Union

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings


class TextCompletionClientBase(ABC):
    """Base class for text completion AI services."""

    @abstractmethod
    async def complete_async(
        self,
        prompt: str,
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> Union[str, List[str]]:
        """
        This is the method that is called from the kernel to get a response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

            Returns:
                Union[str, List[str]] -- A string or list of strings representing the response(s) from the LLM.
        """

    @abstractmethod
    async def complete_stream_async(
        self,
        prompt: str,
        settings: "AIRequestSettings",
        logger: Optional[Any] = None,
    ) -> AsyncGenerator[Union[str, List[str]], None]:
        """
        This is the method that is called from the kernel to get a stream response from a text-optimized LLM.

        Arguments:
            prompt {str} -- The prompt to send to the LLM.
            settings {AIRequestSettings} -- Settings for the request.
            logger {Logger} -- A logger to use for logging (deprecated).

        Yields:
            A stream representing the response(s) from the LLM.
        """
