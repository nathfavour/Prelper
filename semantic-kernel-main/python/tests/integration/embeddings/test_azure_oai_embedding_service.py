# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from openai import AsyncAzureOpenAI

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_azure_text_embedding_service(create_kernel, get_aoai_config):
    kernel = create_kernel

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
    else:
        deployment_name = "text-embedding-ada-002"

    kernel.add_text_embedding_generation_service(
        "aoai-ada",
        sk_oai.AzureTextEmbedding(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        ),
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await kernel.memory.save_information_async("test", id="info1", text="this is a test")
    await kernel.memory.save_reference_async(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_azure_text_embedding_service_with_provided_client(create_kernel, get_aoai_config):
    kernel = create_kernel

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]
    else:
        deployment_name = "text-embedding-ada-002"

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2023-05-15",
        default_headers={"Test-User-X-ID": "test"},
    )

    kernel.add_text_embedding_generation_service(
        "aoai-ada-2",
        sk_oai.AzureTextEmbedding(
            deployment_name=deployment_name,
            async_client=client,
        ),
    )
    kernel.register_memory_store(memory_store=sk.memory.VolatileMemoryStore())

    await kernel.memory.save_information_async("test", id="info1", text="this is a test")
    await kernel.memory.save_reference_async(
        "test",
        external_id="info1",
        text="this is a test",
        external_source_name="external source",
    )


@pytest.mark.asyncio
async def test_batch_azure_embeddings(get_aoai_config):
    # Configure LLM service
    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAIEmbeddings__DeploymentName"]

    else:
        deployment_name = "ada-002"

    embeddings_service = sk_oai.AzureTextEmbedding(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
    )
    texts = ["hello world", "goodbye world"]
    results = await embeddings_service.generate_embeddings_async(texts)
    batch_results = await embeddings_service.generate_embeddings_async(texts, batch_size=1)
    assert len(results) == len(batch_results)
