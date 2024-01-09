# Copyright (c) Microsoft. All rights reserved.

import os

import pytest
from openai import AsyncAzureOpenAI
from test_utils import retry

import semantic_kernel.connectors.ai.open_ai as sk_oai


@pytest.mark.asyncio
async def test_azure_e2e_text_completion_with_skill(setup_tldr_function_for_oai_models, get_aoai_config):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
    else:
        deployment_name = "text-davinci-003"

    print("* Service: Azure OpenAI Text Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
        ),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run_async(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100


@pytest.mark.asyncio
async def test_azure_e2e_text_completion_with_skill_with_provided_client(
    setup_tldr_function_for_oai_models, get_aoai_config
):
    kernel, sk_prompt, text_to_summarize = setup_tldr_function_for_oai_models

    _, api_key, endpoint = get_aoai_config

    if "Python_Integration_Tests" in os.environ:
        deployment_name = os.environ["AzureOpenAI__DeploymentName"]
    else:
        deployment_name = "text-davinci-003"

    print("* Service: Azure OpenAI Text Completion")
    print(f"* Endpoint: {endpoint}")
    print(f"* Deployment: {deployment_name}")

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        azure_deployment=deployment_name,
        api_key=api_key,
        api_version="2023-05-15",
        default_headers={"Test-User-X-ID": "test"},
    )

    # Configure LLM service
    kernel.add_text_completion_service(
        "text_completion",
        sk_oai.AzureTextCompletion(
            deployment_name=deployment_name,
            async_client=client,
        ),
    )

    # Create the semantic function
    tldr_function = kernel.create_semantic_function(sk_prompt, max_tokens=200, temperature=0, top_p=0.5)

    summary = await retry(lambda: kernel.run_async(tldr_function, input_str=text_to_summarize))
    output = str(summary).strip()
    print(f"TLDR using input string: '{output}'")
    assert "First Law" not in output and ("human" in output or "Human" in output or "preserve" in output)
    assert len(output) < 100
