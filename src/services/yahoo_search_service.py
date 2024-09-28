from urllib.parse import quote
import aiohttp
from retry import retry

from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO


class YahooSearchService:
    @staticmethod
    def create_url(search_term: str) -> str:
        """
        Given a search term e.g "menstrual cycle"
        1. Url encode it -> "menstrual+cycle"
        2. Concatenate the base url "https://sg.search.yahoo.com/search?q=" with step 1
        :param search_term:
        :return:

        TODO: Unit test this
        """
        return f"https://sg.search.yahoo.com/search?q={quote(search_term)}"

    @retry(
        exceptions=aiohttp.ClientError,
        tries=5,
        delay=0.01,
        jitter=(-0.01, 0.01),
        backoff=2,
    )
    async def _search(self, user_id: str, search_term: str) -> RawSearchResultsDTO:
        """
        TODO: Integration test this

        Jitter -> Prevent the thundering herd problem;
        - Imagine you have 1,000 servers all failing
        - Imagine all of them retry every 1
        second at the same time to the downstream server
        - Your downstream server will die
        - So to spread out the requests to the downstream server,
        we add a random noise to their retry intervals
        - For API calls, we typically use -0.01s to 0.01s (10 ms)

        Exponential Backoff
        - Retry up to 5 times
        - 2nd try -> 0.01 seconds after 1st try
        - 3rd try -> 0.02 seconds after 2nd try
        - 4th try -> 0.04 seconds after 3rd try
        - 5th try -> 0.08 seconds after 4th try

        Makes a request to a google search url

        Step 1: Make the API call
        - You can run into HTTPError; eg wifi go down
        - Log and Retry the query if it raises a HTTPError

        Step 2: response succeeded
        - status code is 400 (we as the client fucked up)
        - 200 (success)
        - 500 (server error, the google search engine fucked up)
        """
        print(f"Started google_search for {search_term}")
        try:
            """
            catch the request get
            you can commonly get intermittent wifi errors
            when we do, we get a HTTPError
            """
            url: str = YahooSearchService.create_url(search_term)
            headers: dict[str, str] = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            }
            async with aiohttp.ClientSession() as client:
                async with client.get(url, headers=headers, ssl=False) as response:
                    if response.status == 200:
                        # result is the html
                        result: str = await response.text()
                        search_result = RawSearchResultsDTO.create(
                            user_id=user_id, search_term=search_term, result=result
                        )
                        return search_result
                    else:
                        print(
                            f"Response has a non-200 status code: "
                            f"{response.status} for url: {url}"
                        )
                        return RawSearchResultsDTO.create(
                            user_id=user_id, search_term=search_term, result=None
                        )
        except aiohttp.ClientError as e:
            """
            Simplification: assume that all aiohttp.ClientError is retriable
            """
            print(e)
            raise e

    async def yahoo_search(self, user_id: str, search_term: str) -> RawSearchResultsDTO:
        """
        Does two things:
        - Performs the search
        - Persist result into the database

        Unit test this
        - This calls self._search
        - If it raises exception, ensure it creates a dummy result
        (SearchResults.create with results=None)
        - insert_search is always called
        """
        try:
            result: RawSearchResultsDTO = await self._search(user_id, search_term)
        except Exception as e:
            print(f"Ran in error {e}")
            result = RawSearchResultsDTO.create(
                user_id=user_id, search_term=search_term, result=None
            )
        return result
