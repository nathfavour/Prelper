# Copyright (c) Microsoft. All rights reserved.

import logging
import urllib
from typing import List

import aiohttp

from semantic_kernel.connectors.search_engine.connector import ConnectorBase

logger: logging.Logger = logging.getLogger(__name__)


class GoogleConnector(ConnectorBase):
    """
    A search engine connector that uses the Google Custom Search API to perform a web search.
    """

    _api_key: str
    _search_engine_id: str

    def __init__(self, api_key: str, search_engine_id: str, **kwargs) -> None:
        if kwargs.get("logger"):
            logger.warning("The `logger` parameter is deprecated. Please use the `logging` module instead.")
        self._api_key = api_key
        self._search_engine_id = search_engine_id

        if not self._api_key:
            raise ValueError("Google Custom Search API key cannot be null.")

        if not self._search_engine_id:
            raise ValueError("Google search engine ID cannot be null.")

    async def search_async(self, query: str, num_results: str, offset: str) -> List[str]:
        """
        Returns the search results of the query provided by pinging the Google Custom search API.
        Returns `num_results` results and ignores the first `offset`.

        :param query: search query
        :param num_results: the number of search results to return
        :param offset: the number of search results to ignore
        :return: list of search results
        """
        if not query:
            raise ValueError("query cannot be 'None' or empty.")

        if not num_results:
            num_results = 1
        if not offset:
            offset = 0

        num_results = int(num_results)
        offset = int(offset)

        if num_results <= 0:
            raise ValueError("num_results value must be greater than 0.")
        if num_results > 10:
            raise ValueError("num_results value must be less than or equal to 10.")

        if offset < 0:
            raise ValueError("offset must be greater than 0.")

        logger.info(
            f"Received request for google search with \
                params:\nquery: {query}\nnum_results: {num_results}\noffset: {offset}"
        )

        _base_url = "https://www.googleapis.com/customsearch/v1"
        _request_url = (
            f"{_base_url}?q={urllib.parse.quote_plus(query)}"
            f"&key={self._api_key}&cx={self._search_engine_id}"
            f"&num={num_results}&start={offset}"
        )

        logger.info("Sending GET request to Google Search API.")

        async with aiohttp.ClientSession() as session:
            async with session.get(_request_url, raise_for_status=True) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Request successful.")
                    logger.info(f"API Response: {data}")
                    items = data["items"]
                    result = [x["snippet"] for x in items]
                    return result
                else:
                    logger.error(f"Request to Google Search API failed with status code: {response.status}.")
                    return []
