# Copyright (c) Microsoft. All rights reserved.
import json
import logging
import typing as t
from typing import ClassVar

from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext

logger: logging.Logger = logging.getLogger(__name__)


class TextMemorySkill(SKBaseModel):
    COLLECTION_PARAM: ClassVar[str] = "collection"
    RELEVANCE_PARAM: ClassVar[str] = "relevance"
    KEY_PARAM: ClassVar[str] = "key"
    LIMIT_PARAM: ClassVar[str] = "limit"
    DEFAULT_COLLECTION: ClassVar[str] = "generic"
    DEFAULT_RELEVANCE: ClassVar[float] = "0.75"
    DEFAULT_LIMIT: ClassVar[int] = "1"

    # @staticmethod
    @sk_function(
        description="Recall a fact from the long term memory",
        name="recall",
        input_description="The information to retrieve",
    )
    @sk_function_context_parameter(
        name=COLLECTION_PARAM,
        description="The collection to search for information",
        default_value=DEFAULT_COLLECTION,
    )
    @sk_function_context_parameter(
        name=RELEVANCE_PARAM,
        description="The relevance score, from 0.0 to 1.0; 1.0 means perfect match",
        default_value=DEFAULT_RELEVANCE,
    )
    @sk_function_context_parameter(
        name=LIMIT_PARAM,
        description="The maximum number of relevant memories to recall.",
        default_value=DEFAULT_LIMIT,
    )
    async def recall_async(self, ask: str, context: "SKContext") -> str:
        """
        Recall a fact from the long term memory.

        Example:
            sk_context["input"] = "what is the capital of France?"
            {{memory.recall $input}} => "Paris"

        Args:
            ask -- The question to ask the memory
            context -- Contains the 'collection' to search for information
                , the 'relevance' score to use when searching
                and the 'limit' of relevant memories to retrieve.

        Returns:
            The nearest item from the memory store as a string or empty string if not found.
        """

        if context.variables is None:
            raise ValueError("The context doesn't have the variables required to know how to recall memory")
        if context.memory is None:
            raise ValueError("The context doesn't have a memory instance to search")

        collection = context.variables.get(TextMemorySkill.COLLECTION_PARAM, TextMemorySkill.DEFAULT_COLLECTION)
        if not collection:
            raise ValueError("Memory collection not defined for TextMemorySkill")

        relevance = context.variables.get(TextMemorySkill.RELEVANCE_PARAM, TextMemorySkill.DEFAULT_RELEVANCE)
        if not relevance:
            raise ValueError("Relevance value not defined for TextMemorySkill")

        limit = context.variables.get(TextMemorySkill.LIMIT_PARAM, TextMemorySkill.DEFAULT_LIMIT)
        if limit is None or str(limit).strip() == "":
            raise ValueError("Limit value not defined for TextMemorySkill")

        results = await context.memory.search_async(
            collection=collection,
            query=ask,
            limit=int(limit),
            min_relevance_score=float(relevance),
        )
        if results is None or len(results) == 0:
            logger.warning(f"Memory not found in collection: {collection}")
            return ""

        return results[0].text if limit == 1 else json.dumps([r.text for r in results])

    @sk_function(
        description="Save information to semantic memory",
        name="save",
        input_description="The information to save",
    )
    @sk_function_context_parameter(
        name=COLLECTION_PARAM,
        description="The collection to save the information",
        default_value=DEFAULT_COLLECTION,
    )
    @sk_function_context_parameter(
        name=KEY_PARAM,
        description="The unique key to associate with the information",
    )
    async def save_async(self, text: str, context: "SKContext") -> None:
        """
        Save a fact to the long term memory.

        Example:
            sk_context["input"] = "the capital of France is Paris"
            sk_context[TextMemorySkill.KEY_PARAM] = "countryInfo1"
            {{memory.save $input}}

        Args:
            text -- The text to save to the memory
            context -- Contains the 'collection' to save the information
                and unique 'key' to associate with the information
        """

        if context.variables is None:
            raise ValueError("The context doesn't have the variables required to know how to recall memory")
        if context.memory is None:
            raise ValueError("The context doesn't have a memory instance to search")

        collection = context.variables.get(TextMemorySkill.COLLECTION_PARAM, TextMemorySkill.DEFAULT_COLLECTION)
        if not collection:
            raise ValueError("Memory collection not defined for TextMemorySkill")

        key = context.variables.get(TextMemorySkill.KEY_PARAM, None)
        if not key:
            raise ValueError("Memory key not defined for TextMemorySkill")

        await context.memory.save_information_async(collection, text=text, id=key)
