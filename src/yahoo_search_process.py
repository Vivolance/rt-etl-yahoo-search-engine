import asyncio
from asyncio import Future
from threading import Event
from typing import Any

import toml

from src.consumers.consumers import RawSearchTermConsumer
from src.consumers.producers import RawSearchResultsProducer
from src.models.raw_search_results import RawSearchResults, RawSearchResultsRecord
from src.models.raw_search_terms import RawSearchTermsRecord
from src.services.batcher_service import Batcher
from src.services.raw_search_results_dao import RawSearchResultsDAO
from src.services.yahoo_search_service import YahooSearchService


class YahooSearchProcess:
    """
    High-Level Orchestrator
    - Responsible for starting both the consumer and producer
    """

    def __init__(
        self,
        consumer: RawSearchTermConsumer,
        producer: RawSearchResultsProducer,
        batcher: Batcher[RawSearchTermsRecord],
        yahoo_search_service: YahooSearchService,
        dao: RawSearchResultsDAO,
    ) -> None:
        self._consumer: RawSearchTermConsumer = consumer
        self._producer: RawSearchResultsProducer = producer
        self._batcher: Batcher[RawSearchTermsRecord] = batcher
        self._yahoo_search_service: YahooSearchService = yahoo_search_service
        self._dao: RawSearchResultsDAO = dao
        self._shutdown_event: Event = Event()

    async def get_yahoo_search(
        self, record: RawSearchTermsRecord
    ) -> tuple[RawSearchTermsRecord, RawSearchResults]:
        raw_search_result = await self._yahoo_search_service.yahoo_search(
            user_id=record.user_id, search_term=record.search_term
        )
        return record, raw_search_result

    async def start(self) -> None:
        # TODO: Investigate cold start. It takes some time for the consumer to start consuming
        print("Consumer started")
        while not self._shutdown_event.is_set():
            deserialized_messages: list[RawSearchTermsRecord] = self._consumer.consume()
            self._batcher.append_batch(deserialized_messages)
            if self._batcher.batch_ready():
                batch_of_records: list[RawSearchTermsRecord] = self._batcher.get_batch()
                print(f"batch_of_records: {batch_of_records}")
                if batch_of_records:
                    yahoo_search_futures: list[
                        Future[tuple[RawSearchTermsRecord, RawSearchResults]]
                    ] = [
                        asyncio.ensure_future(self.get_yahoo_search(record))
                        for record in batch_of_records
                    ]
                    all_yahoo_search_future: Future[
                        list[tuple[RawSearchTermsRecord, RawSearchResults]]
                    ] = asyncio.gather(*yahoo_search_futures)
                    all_search_results: list[
                        tuple[RawSearchTermsRecord, RawSearchResults]
                    ] = await all_yahoo_search_future
                    await self._dao.insert_many(
                        [output for _, output in all_search_results]
                    )
                    """
                    id: str
                    user_id: str
                    search_term: str
                    result: str | None
                    created_at: SkipValidation[datetime]
                    """
                    all_search_results_records: list[RawSearchResultsRecord] = [
                        RawSearchResultsRecord.create_from_raw_search_term_and_results(
                            input_record=input_record, output_record=output_record
                        )
                        for input_record, output_record in all_search_results
                    ]
                    self._batcher.reset_batch()
                    self._producer.produce(all_search_results_records)
                    self._consumer.commit()


if __name__ == "__main__":
    config: dict[str, Any] = toml.load("src/config/config.toml")
    consumer_config: dict[str, Any] = config["kafka"]["consumer"]["yahoo_search"]
    producer_config: dict[str, Any] = config["kafka"]["producer"]["yahoo_search"]
    formatted_consumer_config: dict[str, Any] = {
        key.replace("_", "."): value for key, value in consumer_config.items()
    }
    formatted_producer_config: dict[str, Any] = {
        key.replace("_", "."): value for key, value in producer_config.items()
    }
    db_config: dict[str, Any] = config["postgres"]
    consumer: RawSearchTermConsumer = RawSearchTermConsumer(formatted_consumer_config)
    producer: RawSearchResultsProducer = RawSearchResultsProducer(
        formatted_producer_config
    )
    batcher: Batcher[RawSearchTermsRecord] = Batcher()
    yahoo_search_service: YahooSearchService = YahooSearchService()
    dao: RawSearchResultsDAO = RawSearchResultsDAO(db_config["connection_string"])
    process: YahooSearchProcess = YahooSearchProcess(
        consumer=consumer,
        producer=producer,
        batcher=batcher,
        yahoo_search_service=yahoo_search_service,
        dao=dao,
    )
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(process.start())
