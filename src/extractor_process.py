import asyncio
from threading import Event
from typing import Any

import toml
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from src.consumers.consumers import RawSearchResultsConsumer
from src.models.dto_data_classes.extracted_search_result_dto import (
    ExtractedSearchResultDTO,
)
from src.models.dto_data_classes.raw_search_results_dto import RawSearchResultsDTO
from src.models.dto_data_classes.status_dto import JobsDTO
from src.models.extractor_data_classes.extracted_search_result import (
    ExtractedSearchResult,
)
from src.models.kafka_records_data_classes.raw_search_results import (
    RawSearchResultsRecord,
)
from src.services.batcher_service import Batcher
from src.services.daos.extracted_search_results_dao import ExtractedSearchResultsDAO
from src.services.daos.raw_search_results_dao import RawSearchResultsDAO
from src.services.daos.status_dao import JobsDAO
from src.services.search_result_extractor import BS4SearchResultExtractor


class ExtractorProcess:
    """
    High-Level Orchestrator
    - Responsible for starting both consumer and producer

    Responsible for reading raw_search_results topic

    get raw_search_results_id and query PG for search results
    extract the structure
    save it into PG
    update your jobs table to COMPLETED

    Consumer:
    - RawSearchResultsConsumer

    DAOs
    - raw search results DAO
    - extracted search results DAO
    - jobs DAO

    Service:
    - Extractor
    """

    def __init__(
        self,
        consumer: RawSearchResultsConsumer,
        batcher: Batcher[RawSearchResultsRecord],
        raw_search_results_dao: RawSearchResultsDAO,
        extracted_search_results_dao: ExtractedSearchResultsDAO,
        jobs_dao: JobsDAO,
        extractor: BS4SearchResultExtractor,
        connection_string: str,
    ) -> None:
        self._consumer: RawSearchResultsConsumer = consumer
        self._batcher: Batcher[RawSearchResultsRecord] = batcher
        self._raw_search_results_dao: RawSearchResultsDAO = raw_search_results_dao
        self._extracted_search_results_dao: ExtractedSearchResultsDAO = (
            extracted_search_results_dao
        )
        self._jobs_dao: JobsDAO = jobs_dao
        self._extractor: BS4SearchResultExtractor = extractor
        self._shutdown_event: Event = Event()
        self._engine: AsyncEngine = create_async_engine(connection_string)

    async def start(self) -> None:
        # TODO: Investigate cold start. It takes some time for the consumer to start consuming
        print("Consumer started")
        while not self._shutdown_event.is_set():
            deserialized_messages: list[RawSearchResultsRecord] = (
                self._consumer.consume()
            )
            self._batcher.append_batch(deserialized_messages)
            if self._batcher.batch_ready():
                batch_of_records: list[RawSearchResultsRecord] = (
                    self._batcher.get_batch()
                )
                print(f"batch_of_records: {batch_of_records}")
                # used to map the raw search results, back to their job ids
                # str -> raw search results id
                # value -> full raw search result record (user id + jobs id)
                raw_results_id_to_record: dict[str, RawSearchResultsRecord] = {
                    record.raw_search_results_id: record for record in batch_of_records
                }
                raw_search_results_ids: list[str] = [
                    record.raw_search_results_id for record in batch_of_records
                ]
                raw_search_results: list[RawSearchResultsDTO] = (
                    await self._raw_search_results_dao.select(raw_search_results_ids)
                )
                all_results_dtos: list[ExtractedSearchResultDTO] = []
                all_jobs_dtos: list[JobsDTO] = []
                print(f"raw_search_results: {len(raw_search_results)}")
                for raw_search_result in raw_search_results:
                    current_job_id: str = raw_results_id_to_record[
                        raw_search_result.id
                    ].job_id
                    print(f"current_job_id: {current_job_id}")
                    current_user_id: str = raw_results_id_to_record[
                        raw_search_result.id
                    ].user_id
                    print(f"current_user_id: {current_user_id}")
                    print(
                        f"raw search result present: {raw_search_result.result is not None}"
                    )
                    extracted_search_results: list[ExtractedSearchResult] = (
                        self._extractor.extract(
                            user_id=raw_search_result.user_id,
                            html=raw_search_result.result,
                        )
                        if raw_search_result.result is not None
                        else []
                    )
                    print(f"extracted_search_results: {extracted_search_results}")
                    results_dto: list[ExtractedSearchResultDTO] = [
                        ExtractedSearchResultDTO.from_search_results(
                            search_results=single_search_result, jobs_id=current_job_id
                        )
                        for single_search_result in extracted_search_results
                    ]
                    all_results_dtos.extend(results_dto)
                    completed_jobs_dto: JobsDTO = JobsDTO.create_completed_job(
                        jobs_id=current_job_id,
                        user_id=current_user_id,
                        raw_search_results_id=raw_search_result.id,
                    )
                    print(f"completed_jobs_dto: {completed_jobs_dto}")
                    all_jobs_dtos.append(completed_jobs_dto)

                async with self._engine.begin() as conn:
                    if all_results_dtos:
                        await self._extracted_search_results_dao.insert_many_transaction(
                            conn, all_results_dtos
                        )
                    if all_jobs_dtos:
                        await self._jobs_dao.insert_many_status_transaction(
                            conn, all_jobs_dtos
                        )

                self._batcher.reset_batch()
                self._consumer.commit()


if __name__ == "__main__":
    config: dict[str, Any] = toml.load("src/config/config.toml")
    consumer_config: dict[str, Any] = config["kafka"]["consumer"]["extractor"]
    formatted_consumer_config: dict[str, Any] = {
        key.replace("_", "."): value for key, value in consumer_config.items()
    }
    db_config: dict[str, Any] = config["postgres"]
    connection_string: str = db_config["connection_string"]
    consumer: RawSearchResultsConsumer = RawSearchResultsConsumer(
        formatted_consumer_config
    )
    batcher: Batcher[RawSearchResultsRecord] = Batcher()
    raw_search_results_dao: RawSearchResultsDAO = RawSearchResultsDAO(connection_string)
    extracted_search_results_dao: ExtractedSearchResultsDAO = ExtractedSearchResultsDAO(
        connection_string
    )
    jobs_dao: JobsDAO = JobsDAO(connection_string)
    extractor: BS4SearchResultExtractor = BS4SearchResultExtractor()
    process = ExtractorProcess(
        consumer=consumer,
        batcher=batcher,
        raw_search_results_dao=raw_search_results_dao,
        extracted_search_results_dao=extracted_search_results_dao,
        jobs_dao=jobs_dao,
        extractor=extractor,
        connection_string=connection_string,
    )
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(process.start())
