# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai

kernel = sk.Kernel()

# Load Azure OpenAI Settings
deployment, api_key, endpoint = sk.azure_openai_settings_from_dot_env()

# For example, AI Search index may contain the following document:

# Emily and David, two passionate scientists, met during a research expedition to Antarctica.
# Bonded by their love for the natural world and shared curiosity, they uncovered a
# groundbreaking phenomenon in glaciology that could potentially reshape our understanding of climate change.

azure_ai_search_settings = sk.azure_aisearch_settings_from_dot_env_as_dict()

# This example index has fields "title", "chunk", and "vector".
# Add fields mapping to the settings.
azure_ai_search_settings["fieldsMapping"] = {
    "titleField": "title",
    "contentFields": ["chunk"],
    "vectorFields": ["vector"],
}
# Add Ada embedding deployment name to the settings and use vector search.
azure_ai_search_settings["embeddingDeploymentName"] = "ada-002"
azure_ai_search_settings["queryType"] = "vector"

# Configure the Azure AI Search index as a data source.
azure_aisearch_datasource = sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureAISearchDataSource(
    parameters=sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureAISearchDataSourceParameters(
        **azure_ai_search_settings
    )
)
azure_chat_with_data_settings = sk_oai.OpenAIChatPromptTemplateWithDataConfig.AzureChatWithDataSettings(
    dataSources=[azure_aisearch_datasource]
)


# When using data, set use_extensions=True and use the 2023-12-01-preview API version.
chat_service = sk_oai.AzureChatCompletion(
    deployment_name=deployment,
    api_key=api_key,
    endpoint=endpoint,
    api_version="2023-12-01-preview",
    use_extensions=True,
)
kernel.add_chat_service("chat-gpt", chat_service)

prompt_config = sk_oai.OpenAIChatPromptTemplateWithDataConfig.from_completion_parameters(
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    data_source_settings=azure_chat_with_data_settings,
)

prompt_template = sk.ChatPromptTemplate("{{$user_input}}", kernel.prompt_template_engine, prompt_config)

prompt_template.add_user_message("Hi there, who are you?")
prompt_template.add_assistant_message("I am an AI assistant here to answer your questions.")

function_config = sk.SemanticFunctionConfig(prompt_config, prompt_template)
chat_function = kernel.register_semantic_function("ChatBot", "Chat", function_config)


async def chat() -> bool:
    context_vars = sk.ContextVariables()

    try:
        user_input = input("User:> ")
        context_vars["user_input"] = user_input
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False

    # Non streaming
    # answer = await kernel.run_async(chat_function, input_vars=context_vars)
    # print(f"Assistant:> {answer}")

    answer = kernel.run_stream_async(chat_function, input_vars=context_vars)
    print("Assistant:> ", end="")
    async for message in answer:
        print(message, end="")
    print("\n")
    return True


async def main() -> None:
    chatting = True
    while chatting:
        chatting = await chat()


if __name__ == "__main__":
    asyncio.run(main())
