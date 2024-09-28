import os
import time
from typing import Any
import requests
from dotenv import load_dotenv
from client.models.client_level_data_classes.output.search_response import (
    SearchResponse,
)
from client.models.client_level_data_classes.output.search_status import ResponseStatus
from client.models.client_level_data_classes.output.single_search_result import (
    SingleSearchResult,
)
from database.tables import JobStatus

load_dotenv()


def _start_search(search_term: str) -> SearchResponse:
    base_url: str = os.getenv("SERVER_URL")
    try:
        response: requests.Response = requests.post(
            f"{base_url}/search", json={"search_term": search_term, "user_id": "1"}
        )
        if response.status_code != 200:
            raise Exception(
                f"Status code unexpectedly not 200 when starting search: {response.status_code}, {response.text}"
            )
        response_json: dict[str, Any] = response.json()
        return SearchResponse.model_validate(response_json)
    except Exception as e:
        print(f"Exception raised when starting search: {e}")
        raise e


def _check_status(job_id: str) -> ResponseStatus:
    base_url: str = os.getenv("SERVER_URL")
    try:
        response: requests.Response = requests.get(
            f"{base_url}/status", json={"job_id": job_id}
        )
        if response.status_code != 200:
            raise Exception(
                f"_check_status unexpectedly not 200 when getting job result: {response.status_code}"
            )
        response_json: dict[str, Any] = response.json()
        return ResponseStatus.model_validate(response_json)
    except Exception as e:
        print(f"Exception raised when querying for status: {e}")
        raise e


def _get_job_result(job_id: str) -> list[SingleSearchResult]:
    base_url: str = os.getenv("SERVER_URL")
    try:
        response: requests.Response = requests.get(
            f"{base_url}/result", json={"job_id": job_id}
        )
        if response.status_code != 200:
            raise Exception(
                f"Status code unexpectedly not 200 when getting job result: {response.status_code}"
            )
        response_json: list[dict[str, Any]] = response.json()
        response_results: list[SingleSearchResult] = [
            SingleSearchResult.model_validate(single_result)
            for single_result in response_json
        ]
        return response_results
    except Exception as e:
        print(f"Exception raised when querying for result: {e}")
        raise e


def get_result(search_term: str) -> list[SingleSearchResult]:
    """
    1. Fires query
    2. Suspend till query is done
    3. Return result
    """
    print(f"search_term: {search_term}")
    search_response: SearchResponse = _start_search(search_term)
    while True:
        job_id: str = search_response.job_id
        response_status: ResponseStatus = _check_status(job_id)
        status = response_status.status
        if status == JobStatus.COMPLETED:
            results: list[SingleSearchResult] = _get_job_result(job_id)
            return results
        elif status == JobStatus.IN_PROGRESS:
            time.sleep(1)
        else:
            raise Exception(
                f"Unexpected error occured when getting result: Status {status}"
            )
