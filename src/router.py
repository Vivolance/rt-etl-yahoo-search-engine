import signal
import time
from threading import Thread, Event
from types import FrameType

from aiohttp.web import Request, Response
from typing import Any
import json


from src.consumers.producers import RawSearchTermsProducer
from src.models.raw_search_terms import RawSearchTermsRecord
from src.models.status_dto import JobsDTO
from src.services.batcher_service import Batcher
from src.services.status_dao import JobsDAO
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
    def __init__(self, status_dao: JobsDAO, producer_config: dict[str, str]) -> None:
        self._status_dao: JobsDAO = status_dao
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
