# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from typing import Any, Dict, Mapping, Optional

from openai import AsyncOpenAI
from pydantic import Field, validate_call

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.open_ai.const import (
    USER_AGENT,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_handler import (
    OpenAIHandler,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_model_types import (
    OpenAIModelTypes,
)
from semantic_kernel.connectors.telemetry import APP_INFO

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIConfigBase(OpenAIHandler):
    @validate_call(config=dict(arbitrary_types_allowed=True))
    def __init__(
        self,
        ai_model_id: str = Field(min_length=1),
        api_key: Optional[str] = Field(min_length=1),
        ai_model_type: Optional[OpenAIModelTypes] = OpenAIModelTypes.CHAT,
        org_id: Optional[str] = None,
        default_headers: Optional[Mapping[str, str]] = None,
        async_client: Optional[AsyncOpenAI] = None,
        log: Optional[Any] = None,
    ) -> None:
        """Initialize a client for OpenAI services.

        This constructor sets up a client to interact with OpenAI's API, allowing for
        different types of AI model interactions, like chat or text completion.

        Arguments:
            ai_model_id {str} -- OpenAI model identifier. Must be non-empty.
                Default to a preset value.
            api_key {Optional[str]} -- OpenAI API key for authentication.
                Must be non-empty. (Optional)
            ai_model_type {Optional[OpenAIModelTypes]} -- The type of OpenAI
                model to interact with. Defaults to CHAT.
            org_id {Optional[str]} -- OpenAI organization ID. This is optional
                unless the account belongs to multiple organizations.
            default_headers {Optional[Mapping[str, str]]} -- Default headers
                for HTTP requests. (Optional)

        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        # Merge APP_INFO into the headers if it exists
        merged_headers = default_headers.copy() if default_headers else {}
        if APP_INFO:
            merged_headers[USER_AGENT] = json.dumps(APP_INFO)

        if not async_client:
            if not api_key:
                raise AIException(
                    AIException.ErrorCodes.InvalidConfiguration,
                    "Please provide an api_key",
                )
            async_client = AsyncOpenAI(
                api_key=api_key,
                organization=org_id,
                default_headers=merged_headers,
            )

        super().__init__(
            ai_model_id=ai_model_id,
            client=async_client,
            ai_model_type=ai_model_type,
        )

    def to_dict(self) -> Dict[str, str]:
        """
        Create a dict of the service settings.
        """
        client_settings = {
            "api_key": self.client.api_key,
            "default_headers": {k: v for k, v in self.client.default_headers.items() if k != USER_AGENT},
        }
        if self.client.organization:
            client_settings["org_id"] = self.client.organization
        base = self.model_dump(
            exclude={
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "api_type",
                "ai_model_type",
                "client",
            },
            by_alias=True,
            exclude_none=True,
        )
        base.update(client_settings)
        return base

    def get_model_args(self) -> Dict[str, Any]:
        return {
            "model": self.ai_model_id,
        }
