import json
from typing import Any, Generic, TypeVar, Type

from confluent_kafka import Consumer, Message
from pydantic import BaseModel

from src.models.kafka_records_data_classes.raw_search_results import (
    RawSearchResultsRecord,
)
from src.models.kafka_records_data_classes.raw_search_terms import RawSearchTermsRecord

ConsumerRecord = TypeVar("ConsumerRecord", bound=BaseModel)


class GenericConsumer(Generic[ConsumerRecord]):
    def __init__(
        self,
        consumer_config: dict[str, Any],
        topic_name: str,
        model: Type[ConsumerRecord],
    ) -> None:
        self._consumer: Consumer = Consumer(consumer_config)
        self._topic_name: str = topic_name
        self._consumer.subscribe([self._topic_name])
        self._model: Type[ConsumerRecord] = model  # Pass the Pydantic model class

    def consume(self) -> list[ConsumerRecord]:
        messages: list[Message] = self._consumer.consume(num_messages=1, timeout=1)
        deserialized_messages: list[ConsumerRecord] = self.deserialize_batch(messages)
        return deserialized_messages

    def deserialize_batch(self, messages: list[Message]) -> list[ConsumerRecord]:
        batch_messages: list[ConsumerRecord] = []
        for raw_message in messages:
            # a single raw message is a list of str
            message_bytes: str | bytes | None = raw_message.value()
            if not isinstance(message_bytes, bytes):
                raise Exception(
                    f"message_bytes: {message_bytes} unexpected not of type bytes"
                )
            message_str: str = message_bytes.decode("utf-8")
            raw_message_list: list[dict[str, Any]] = json.loads(message_str)
            message_list: list[ConsumerRecord] = []
            for single_message_dict in raw_message_list:
                try:
                    single_record: ConsumerRecord = self._model.model_validate(
                        single_message_dict
                    )
                    message_list.append(single_record)
                except Exception as err:
                    print(err)
                    print(single_message_dict)
                    raise
            batch_messages.extend(message_list)
        return batch_messages

    def commit(self) -> None:
        self._consumer.commit()


class RawSearchTermConsumer(GenericConsumer[RawSearchTermsRecord]):
    """
    Consumes from `raw_search_terms` topic

    Pass the search terms from the record, to YahooSearchService

    Save the results into `raw_search_terms` table
    """

    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="raw_search_terms",
            model=RawSearchTermsRecord,
        )


class RawSearchResultsConsumer(GenericConsumer[RawSearchResultsRecord]):
    def __init__(self, consumer_config: dict[str, Any]) -> None:
        super().__init__(
            consumer_config=consumer_config,
            topic_name="raw_search_results",
            model=RawSearchResultsRecord,
        )
