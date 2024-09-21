import signal
import time
from threading import Thread, Event
from types import FrameType

from aiohttp.web import Request, Response
from typing import Any
import json

from src.models.raw_search_terms import RawSearchTermsRecord
from src.models.status_dto import JobsDTO
from src.services.status_dao import JobsDAO
from queue import Queue
from confluent_kafka import Producer


class ProducerThread(Thread):
    def __init__(
        self,
        queue: Queue,
        producer_config: dict[str, str],
    ) -> None:
        """
        Listens to a queue of records to `raw_search_terms`
        For each record in the queue, produce it to the topic
        """
        super().__init__()
        self._queue: Queue = queue
        self._shutdown_event: Event = Event()
        self._producer: Producer = Producer(producer_config)
        self._topic_name: str = "raw_search_terms"
        self._batch: list[str] = []
        self._batch_size: int = 100
        # start of batch
        self._batch_start: float = (
            -1
        )  # this will be set at the start of the thread again
        self._batch_timeout_s: int = 1

    def reset_batch(self) -> None:
        """
        Resets the batch
        - Clear the batch list
        - Reset the batch start
        """
        self._batch.clear()
        self._batch_start = time.perf_counter()

    def flush_producer(self) -> None:
        self._producer.flush()

    def batch_ready(self) -> bool:
        """
        Case 1: current time - batch_start > _batch_timeout_s
        - produce

        Case 2: batch_size == 100
        - produce

        return False
        """
        hit_timeout: bool = (
            time.perf_counter() - self._batch_start > self._batch_timeout_s
        )
        hit_batch_size: bool = len(self._batch) == self._batch_size
        return hit_timeout or hit_batch_size

    def _run_impl(self) -> None:
        self._batch_start = time.perf_counter()
        while not self._shutdown_event.is_set():
            record: RawSearchTermsRecord = self._queue.get()
            record_dict: dict[str, str] = record.model_dump()
            record_str: str = json.dumps(record_dict)
            self._batch.append(record_str)
            batch_is_ready: bool = self.batch_ready()
            if batch_is_ready:
                serialized_batch: str = json.dumps(self._batch)
                self._producer.produce(topic=self._topic_name, value=serialized_batch)
                # wait for the batch of messages to be produced successfully
                self.flush_producer()
                self.reset_batch()
        # at this point, the shutdown has occurred
        self.flush_producer()

    def run(self) -> None:
        try:
            self._run_impl()
        except Exception as e:
            print(f"Encountered Exception: {e}")
        finally:
            # always flush, even if something goes wrong
            self.flush_producer()

    def stop(self) -> None:
        self._shutdown_event.set()


class Router:
    def __init__(self, status_dao: JobsDAO, producer_config: dict[str, str]) -> None:
        self._status_dao: JobsDAO = status_dao
        self._queue: Queue = Queue()
        self._producer_thread = ProducerThread(
            queue=self._queue, producer_config=producer_config
        )
        # start the producer thread
        self._producer_thread.start()

    async def search(self, request: Request) -> Response:
        try:
            body: dict[str, Any] = await request.json()
        except Exception as err:
            print(f"Unable to parse body with err: {err}")
            return Response(status=500, text=f"Unable to parse body with err: {err}")

        # validation of client payload
        search_term: str | None = body.get("search_term")
        if search_term is None:
            return Response(status=400, text="Search term is empty")
        user_id: str | None = body.get("user_id")
        if user_id is None:
            return Response(status=400, text="User id is empty")

        # Step 1: Save job id into Postgres
        status_dto: JobsDTO = JobsDTO.new(user_id=user_id)
        await self._status_dao.insert_status(status_dto)
        response_body: dict[str, Any] = {
            "job_id": status_dto.id,
            "search_term": search_term,
        }
        raw_search_terms_record: RawSearchTermsRecord = RawSearchTermsRecord(
            user_id=user_id,
            search_term=search_term,
            job_id=status_dto.id,
            job_created_at=status_dto.created_at,
        )
        # Step 2: Produce to background thread
        self._queue.put(raw_search_terms_record)

        serialized_body = json.dumps(response_body)
        return Response(text=serialized_body)

    async def status(self, request: Request) -> Response:
        body: dict[str, Any] = {"status": "In Progress"}
        serialized_body = json.dumps(body)
        return Response(text=serialized_body)

    async def result(self, request: Request) -> Response:
        body: dict[str, Any] = {"result": [{"title": "Coffee Bean is the best"}]}
        serialized_body = json.dumps(body)
        return Response(text=serialized_body)

    def graceful_shutdown(self) -> None:
        def stop_producer_thread(signum: int, stack: FrameType | None) -> Any:
            print(f"Encountered signum: {signum}")
            print("Shutting down background thread:")
            self._producer_thread.stop()

        signal.signal(signal.SIGINT, stop_producer_thread)
        signal.signal(signal.SIGTERM, stop_producer_thread)
