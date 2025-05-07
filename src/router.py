import signal
import time
from threading import Thread, Event
from types import FrameType

from aiohttp.web import Request, Response
from typing import Any
import json

from aiohttp.web_exceptions import HTTPBadRequest
from pydantic import ValidationError

from database.tables import JobStatus
from src.consumers.producers import RawSearchTermsProducer
from src.models.dto_data_classes.extracted_search_result_dto import (
    ExtractedSearchResultDTO,
)
from src.models.kafka_records_data_classes.raw_search_terms import RawSearchTermsRecord
from src.models.dto_data_classes.status_dto import JobsDTO
from src.models.service_level_data_classes.input.result_input import ResultInput
from src.models.service_level_data_classes.input.search_input import SearchInput
from src.models.service_level_data_classes.input.status_input import StatusInput
from src.models.service_level_data_classes.output.search_response import SearchResponse
from src.models.service_level_data_classes.output.search_status import ResponseStatus
from src.services.batcher_service import Batcher
from src.services.daos.extracted_search_results_dao import ExtractedSearchResultsDAO
from src.services.daos.status_dao import JobsDAO
from queue import Queue


class ProducerThread(Thread):
    def __init__(self, queue: Queue, producer: RawSearchTermsProducer) -> None:
        """
        Listens to a queue of records to `raw_search_terms`
        For each record in the queue, produce it to the topic
        """
        super().__init__()
        self._queue: Queue = queue
        self._shutdown_event: Event = Event()
        self._batcher: Batcher[RawSearchTermsRecord] = Batcher()
        self._producer: RawSearchTermsProducer = producer

    def _run_impl(self) -> None:
        self._batch_start = time.perf_counter()
        while not self._shutdown_event.is_set():
            record: RawSearchTermsRecord = self._queue.get()
            self._batcher.append(record)
            if self._batcher.batch_ready():
                batch: list[RawSearchTermsRecord] = self._batcher.get_batch()
                # wait for the batch of messages to be produced successfully
                self._producer.produce(batch)
                self._producer.flush_producer()
                self._batcher.reset_batch()
        # at this point, the shutdown has occurred
        self._producer.flush_producer()

    def run(self) -> None:
        try:
            self._run_impl()
        except Exception as e:
            print(f"Encountered Exception: {e}")
        finally:
            # always flush, even if something goes wrong
            self._producer.flush_producer()

    def stop(self) -> None:
        self._shutdown_event.set()


class Router:
    def __init__(
        self,
        status_dao: JobsDAO,
        extracted_search_results_dao: ExtractedSearchResultsDAO,
        producer_config: dict[str, str],
    ) -> None:
        self._jobs_dao: JobsDAO = status_dao
        self._extracted_search_results_dao: ExtractedSearchResultsDAO = (
            extracted_search_results_dao
        )
        self._queue: Queue = Queue()
        self._producer: RawSearchTermsProducer = RawSearchTermsProducer(
            producer_config=producer_config
        )
        self._producer_thread = ProducerThread(
            queue=self._queue, producer=self._producer
        )
        # start the producer thread
        self._producer_thread.start()

    async def search(self, request: Request) -> Response:
        try:
            # awaitable because calling .json() on a request reads the header and body from the network socket, which
            # might still be streaming in from the client
            body: dict[str, Any] = await request.json()
            search_input: SearchInput = SearchInput.model_validate(body)
        except json.JSONDecodeError:
            raise HTTPBadRequest(reason="Invalid JSON payload")
        except ValidationError as err:
            return Response(status=400, text=f"Failed to parse input with error: {err}")
        except Exception as err:
            print(f"Unable to parse body with err: {err}")
            return Response(status=500, text=f"Unable to parse body with err: {err}")

        # validation of client payload
        search_term: str = search_input.search_term
        user_id: str = search_input.user_id

        # Step 1: Save job id into Postgres
        status_dto: JobsDTO = JobsDTO.create_job(user_id=user_id)
        await self._jobs_dao.insert_status(status_dto)
        response_body: SearchResponse = SearchResponse(
            job_id=status_dto.jobs_id, search_term=search_term
        )
        raw_search_terms_record: RawSearchTermsRecord = RawSearchTermsRecord(
            user_id=user_id,
            search_term=search_term,
            job_id=status_dto.jobs_id,
            job_created_at=status_dto.created_at,
        )
        # Step 2: Produce to background thread
        self._queue.put(raw_search_terms_record)

        serialized_body_dict: dict[str, Any] = response_body.model_dump()
        serialized_body: str = json.dumps(serialized_body_dict)
        # Return a response with the job_id to the user so that the user can query for its status
        return Response(text=serialized_body)

    async def status(self, request: Request) -> Response:
        """
        {
            "job_id": "1",
            "status": "IN_PROGRESS"
        }
        IN_PROGRESS, COMPLETED, CANCELLED, FAILED
        """
        try:
            request_params: dict[str, Any] = await request.json()
            status_input: StatusInput = StatusInput.model_validate(request_params)
        except json.JSONDecodeError:
            raise HTTPBadRequest(reason="Invalid JSON payload")
        except ValidationError as err:
            return Response(status=400, text=f"Failed to parse input with error: {err}")
        except Exception as err:
            print(f"Unable to parse body with err: {err}")
            return Response(status=500, text=f"Unable to parse body with err: {err}")

        jobs_dto: JobsDTO | None = await self._jobs_dao.read_status(status_input.job_id)
        if jobs_dto is None:
            return Response(status=400, text=f"Invalid jobs_id: {status_input.job_id}")

        body: ResponseStatus = ResponseStatus(
            job_id=jobs_dto.jobs_id, status=jobs_dto.job_status
        )
        serialized_status_dict: dict[str, Any] = body.model_dump()
        serialized_status_str = json.dumps(serialized_status_dict)
        return Response(text=serialized_status_str)

    async def result(self, request: Request) -> Response:
        try:
            request_params: dict[str, Any] = await request.json()
            result_input: ResultInput = ResultInput.model_validate(request_params)
        except json.JSONDecodeError:
            raise HTTPBadRequest(reason="Invalid JSON payload")
        except ValidationError as err:
            return Response(status=400, text=f"Failed to parse input with error: {err}")
        except Exception as err:
            print(f"Unable to parse body with err: {err}")
            return Response(status=500, text=f"Unable to parse body with err: {err}")

        jobs_dto: JobsDTO | None = await self._jobs_dao.read_status(result_input.job_id)
        if jobs_dto is None:
            return Response(status=400, text=f"Invalid jobs_id: {result_input.job_id}")
        elif jobs_dto.job_status != JobStatus.COMPLETED:
            return Response(
                status=400,
                text=f"jobs_id not completed: {result_input.job_id}. job_status: {jobs_dto.job_status}",
            )

        results: list[ExtractedSearchResultDTO] = (
            await self._extracted_search_results_dao.fetch(result_input.job_id)
        )
        serialized_results: list[dict[str, Any]] = [
            single_result.model_dump() for single_result in results
        ]
        serialized_body = json.dumps(serialized_results)
        return Response(text=serialized_body)

    async def healthcheck(self, request: Request) -> Response:
        return Response(text="pong", status=200)

    def graceful_shutdown(self) -> None:
        def stop_producer_thread(signum: int, stack: FrameType | None) -> Any:
            print(f"Encountered signum: {signum}")
            print("Shutting down background thread:")
            self._producer_thread.stop()

        signal.signal(signal.SIGINT, stop_producer_thread)
        signal.signal(signal.SIGTERM, stop_producer_thread)
