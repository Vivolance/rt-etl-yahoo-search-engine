from typing import TypeVar, Generic
import json

from pydantic import BaseModel

from confluent_kafka import Producer

from src.models.raw_search_results import RawSearchResultsRecord
from src.models.raw_search_terms import RawSearchTermsRecord

ProduceMessage = TypeVar("ProduceMessage", bound=BaseModel)


class AbstractProducer(Generic[ProduceMessage]):
    def __init__(self, producer_config: dict[str, str], topic_name: str) -> None:
        self._producer: Producer = Producer(producer_config)
        self._topic_name: str = topic_name

    def produce(self, batch: list[ProduceMessage]) -> None:
        serialized_batch: str = json.dumps(
            [single_item.model_dump() for single_item in batch]
        )
        self._producer.produce(topic=self._topic_name, value=serialized_batch)

    def flush_producer(self) -> None:
        self._producer.flush()


class RawSearchTermsProducer(AbstractProducer[RawSearchTermsRecord]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(producer_config=producer_config, topic_name="raw_search_terms")


class RawSearchResultsProducer(AbstractProducer[RawSearchResultsRecord]):
    def __init__(self, producer_config: dict[str, str]) -> None:
        super().__init__(
            producer_config=producer_config, topic_name="raw_search_results"
        )
