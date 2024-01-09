# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, Optional, Tuple, Union

from dotenv import dotenv_values


def openai_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the OpenAI API key and organization ID from the .env file.

    Returns:
        Tuple[str, str]: The OpenAI API key, the OpenAI organization ID
    """

    config = dotenv_values(".env")
    api_key = config.get("OPENAI_API_KEY", None)
    org_id = config.get("OPENAI_ORG_ID", None)

    assert api_key, "OpenAI API key not found in .env file"

    # It's okay if the org ID is not found (not required)
    return api_key, org_id


def azure_openai_settings_from_dot_env(
    include_deployment: bool = True, include_api_version: bool = False
) -> Union[Tuple[str, str, str], Tuple[str, str, str, str]]:
    """
    Reads the Azure OpenAI API key and endpoint from the .env file.

    Arguments:
        include_deployment {bool} -- Whether to include the deployment name in the return value
        include_api_version {bool} -- Whether to include the API version in the return value,
            when set to True, this will also make the output a Tuple[str, str, str, str].

    Returns:
        Union[Tuple[str, str, str], Tuple[str, str, str, str]]: The deployment name (or empty), Azure OpenAI API key,
          the endpoint and optionally the api version
    """

    deployment, api_key, endpoint, api_version = None, None, None, None
    config = dotenv_values(".env")
    deployment = config.get("AZURE_OPENAI_DEPLOYMENT_NAME", None)
    api_key = config.get("AZURE_OPENAI_API_KEY", None)
    endpoint = config.get("AZURE_OPENAI_ENDPOINT", None)
    api_version = config.get("AZURE_OPENAI_API_VERSION", None)

    # Azure requires the deployment name, the API key and the endpoint URL.
    if include_deployment:
        assert deployment is not None, "Azure OpenAI deployment name not found in .env file"
    if include_api_version:
        assert api_version is not None, "Azure OpenAI API version not found in .env file"

    assert api_key, "Azure OpenAI API key not found in .env file"
    assert endpoint, "Azure OpenAI endpoint not found in .env file"

    if include_api_version:
        return deployment or "", api_key, endpoint, api_version or ""
    return deployment or "", api_key, endpoint


def azure_openai_settings_from_dot_env_as_dict(
    include_deployment: bool = True, include_api_version: bool = False
) -> Dict[str, str]:
    """
    Reads the Azure OpenAI API key and endpoint from the .env file.

    Returns:
        Dict[str, str]: The deployment name (or empty), Azure OpenAI API key,
        endpoint and api version (or empty)
    """
    (
        deployment_name,
        api_key,
        endpoint,
        api_version,
    ) = azure_openai_settings_from_dot_env(include_deployment, include_api_version)
    ret = {
        "api_key": api_key,
        "endpoint": endpoint,
    }
    if include_deployment:
        ret["deployment_name"] = deployment_name
    if include_api_version:
        ret["api_version"] = api_version
    return ret


def postgres_settings_from_dot_env() -> str:
    """Reads the Postgres connection string from the .env file.

    Returns:
        str: The Postgres connection string
    """
    connection_string = None
    config = dotenv_values(".env")
    connection_string = config.get("POSTGRES_CONNECTION_STRING", None)

    assert connection_string, "Postgres connection string not found in .env file"

    return connection_string


def pinecone_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the Pinecone API key and Environment from the .env file.
    Returns:
        Tuple[str, str]: The Pinecone API key, the Pinecone Environment
    """

    api_key, environment = None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
            if line.startswith("PINECONE_API_KEY"):
                parts = line.split("=")[1:]
                api_key = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("PINECONE_ENVIRONMENT"):
                parts = line.split("=")[1:]
                environment = "=".join(parts).strip().strip('"')
                continue

    assert api_key, "Pinecone API key not found in .env file"
    assert environment, "Pinecone environment not found in .env file"

    return api_key, environment


def weaviate_settings_from_dot_env() -> Tuple[Optional[str], str]:
    """
    Reads the Weaviate API key and URL from the .env file.

    Returns:
        Tuple[str, str]: The Weaviate API key, the Weaviate URL
    """

    config = dotenv_values(".env")
    api_key = config.get("WEAVIATE_API_KEY", None)
    url = config.get("WEAVIATE_URL", None)

    # API key not needed for local Weaviate deployment, URL still needed
    assert url is not None, "Weaviate instance URL not found in .env file"

    return api_key, url


def bing_search_settings_from_dot_env() -> str:
    """Reads the Bing Search API key from the .env file.

    Returns:
        Tuple[str, str]: The Bing Search API key, the Bing Search endpoint
    """

    api_key = None
    config = dotenv_values(".env")
    api_key = config.get("BING_API_KEY", None)

    assert api_key is not None, "Bing Search API key not found in .env file"

    return api_key


def mongodb_atlas_settings_from_dot_env() -> str:
    """Returns the Atlas MongoDB Connection String from the .env file.

    Returns:
        str: MongoDB Connection String URI
    """

    config = dotenv_values(".env")
    uri = config.get("MONGODB_ATLAS_CONNECTION_STRING")
    assert uri is not None, "MongoDB Connection String not found in .env file"

    return uri


def google_palm_settings_from_dot_env() -> str:
    """
    Reads the Google PaLM API key from the .env file.

    Returns:
        str: The Google PaLM API key
    """

    config = dotenv_values(".env")
    api_key = config.get("GOOGLE_PALM_API_KEY", None)

    assert api_key is not None, "Google PaLM API key not found in .env file"

    return api_key


def azure_cosmos_db_settings_from_dot_env() -> Tuple[str, str]:
    """
    Reads the Azure CosmosDB environment variables for the .env file.
    Returns:
        dict: The Azure CosmosDB environment variables
    """
    config = dotenv_values(".env")
    cosmos_api = config.get("AZCOSMOS_API")
    cosmos_connstr = config.get("AZCOSMOS_CONNSTR")

    assert cosmos_connstr is not None, "Azure Cosmos Connection String not found in .env file"

    return cosmos_api, cosmos_connstr


def redis_settings_from_dot_env() -> str:
    """Reads the Redis connection string from the .env file.

    Returns:
        str: The Redis connection string
    """
    config = dotenv_values(".env")
    connection_string = config.get("REDIS_CONNECTION_STRING", None)

    assert connection_string is not None, "Redis connection string not found in .env file"

    return connection_string


def azure_aisearch_settings_from_dot_env(
    include_index_name=False,
) -> Union[Tuple[str, str], Tuple[str, str, str]]:
    """
    Reads the Azure AI Search environment variables for the .env file.

    Returns:
        Tuple[str, str]: Azure AI Search API key, the Azure AI Search URL
    """
    config = dotenv_values(".env")
    api_key = config.get("AZURE_AISEARCH_API_KEY", None)
    url = config.get("AZURE_AISEARCH_URL", None)

    assert url is not None, "Azure AI Search URL not found in .env file"
    assert api_key is not None, "Azure AI Search API key not found in .env file"

    if not include_index_name:
        return api_key, url
    else:
        index_name = config.get("AZURE_AISEARCH_INDEX_NAME", None)
        assert index_name is not None, "Azure AI Search index name not found in .env file"
        return api_key, url, index_name


def azure_aisearch_settings_from_dot_env_as_dict() -> Dict[str, str]:
    """
    Reads the Azure AI Search environment variables including index name from the .env file.

    Returns:
        Dict[str, str]: the Azure AI search environment variables
    """
    api_key, url, index_name = azure_aisearch_settings_from_dot_env(include_index_name=True)
    return {"key": api_key, "endpoint": url, "indexName": index_name}
