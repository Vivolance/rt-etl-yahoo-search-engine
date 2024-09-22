import asyncio
import json
from asyncio import Future
from threading import Event
from typing import Any

import toml
from confluent_kafka import Consumer, Message

from src.models.raw_search_results import RawSearchResults
from src.models.raw_search_terms import RawSearchTermsRecord
from src.services.batcher_service import Batcher
from src.services.raw_search_results_dao import RawSearchResultsDAO
from src.services.yahoo_search_service import YahooSearchService


class YahooSearchProcess:
    """
    High-Level Orchestrator
    - Responsible for starting both the consumer and producer
    """


class YahooSearchConsumer:
    """
    Consumes from `yahoo_search_terms` topic

    Pass the search terms from the record, to YahooSearchService

    Save the results into `raw_search_result` table
    """

    def __init__(
        self, consumer_config: dict[str, Any], db_config: dict[str, Any]
    ) -> None:
        self._consumer: Consumer = Consumer(consumer_config)
        self._shutdown_event: Event = Event()
        self._batcher: Batcher[RawSearchTermsRecord] = Batcher()
        self._topic_name: str = "raw_search_terms"
        self._yahoo_search_service: YahooSearchService = YahooSearchService()
        connection_string: str = db_config["connection_string"]
        self._raw_search_results_dao: RawSearchResultsDAO = RawSearchResultsDAO(
            connection_string
        )

    def deserialize_batch(self, messages: list[Message]) -> list[RawSearchTermsRecord]:
        batch_messages: list[RawSearchTermsRecord] = []
        if messages:
            for raw_message in messages:
                # a single raw message is a list of str
                message_bytes: bytes = raw_message.value()
                message_str: str = message_bytes.decode("utf-8")
                raw_message_list: list[dict[str, Any]] = json.loads(message_str)
                message_list: list[RawSearchTermsRecord] = []
                for single_message_dict in raw_message_list:
                    try:
                        single_record: RawSearchTermsRecord = (
                            RawSearchTermsRecord.model_validate(single_message_dict)
                        )
                        message_list.append(single_record)
                    except Exception as err:
                        print(err)
                        print(single_message_dict)
                        raise
                batch_messages.extend(message_list)
        return batch_messages

    async def start(self) -> None:
        # TODO: Investigate cold start. It takes some time for the consumer to start consuming
        self._consumer.subscribe(["raw_search_terms"])
        print("Consumer started")
        while not self._shutdown_event.is_set():
            messages: list[Message] = self._consumer.consume(num_messages=1, timeout=1)
            deserialized_messages: list[RawSearchTermsRecord] = self.deserialize_batch(
                messages
            )
            print(f"deserialized_messages: {deserialized_messages}")
            self._batcher.append_batch(deserialized_messages)
            if self._batcher.batch_ready():
                batch_of_records: list[RawSearchTermsRecord] = self._batcher.get_batch()
                if batch_of_records:
                    yahoo_search_futures: list[Future[RawSearchResults]] = [
                        asyncio.ensure_future(
                            self._yahoo_search_service.yahoo_search(
                                user_id=record.user_id, search_term=record.search_term
                            )
                        )
                        for record in batch_of_records
                    ]
                    all_yahoo_search_future: Future[list[RawSearchResults]] = asyncio.gather(
                        *yahoo_search_futures
                    )
                    all_search_results: list[RawSearchResults] = await all_yahoo_search_future
                    await self._raw_search_results_dao.insert_many(all_search_results)
                    self._batcher.reset_batch()
                    self._consumer.commit()


class YahooSearchProducer:
    """
    Produces full record to `yahoo_search_results`
    """

    pass


if __name__ == "__main__":
    config: dict[str, Any] = toml.load("src/config/config.toml")
    yahoo_search_consumer_config: dict[str, Any] = config["kafka"]["consumer"][
        "yahoo_search"
    ]
    formatted_yahoo_search_consumer_config: dict[str, Any] = {
        key.replace("_", "."): value
        for key, value in yahoo_search_consumer_config.items()
    }
    db_config: dict[str, Any] = config["postgres"]
    print(formatted_yahoo_search_consumer_config)
    consumer: YahooSearchConsumer = YahooSearchConsumer(
        formatted_yahoo_search_consumer_config, db_config
    )
    event_loop = asyncio.new_event_loop()
    event_loop.run_until_complete(consumer.start())
