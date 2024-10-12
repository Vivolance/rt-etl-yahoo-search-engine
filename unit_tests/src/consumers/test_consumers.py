import json
import time
import uuid
from concurrent.futures import Future, as_completed
from datetime import datetime
from typing import Generator

from asyncpg import Record

from src.consumers.consumers import GenericConsumer
from src.models.kafka_records_data_classes.raw_search_terms import RawSearchTermsRecord
import pytest
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import (
    NewTopic,
    Producer,
    KafkaError,
    KafkaException,
    Consumer,
)


@pytest.fixture
def producer() -> Producer:
    return Producer({"bootstrap.servers": "localhost:29092"})


@pytest.fixture
def admin_client() -> AdminClient:
    return AdminClient({"bootstrap.servers": "localhost:29092"})


@pytest.fixture()
def topic_name() -> str:
    return f"raw_search_terms_{uuid.uuid4()}"


@pytest.fixture
def dummy_records() -> list[RawSearchTermsRecord]:
    return [
        RawSearchTermsRecord(
            user_id=str(uuid.uuid4()),
            search_term="Starbucks",
            job_id=str(uuid.uuid4()),
            job_created_at=datetime(year=2024, month=10, day=12),
        )
    ]


@pytest.fixture
def setup_and_teardown_test_consume(
    admin_client: AdminClient,
    topic_name: str,
    producer: Producer,
    dummy_records: list[RawSearchTermsRecord],
) -> Generator[None, None, None]:
    """
    1. Prepare
    - Create a topic (should have a unique name)
    - "raw-search-term_uuid.uuid4()"
    - publish a RawSearchRecord

    yield to Step 2, 3

    4. Teardown
    - Delete the topic
    """

    def create_topic() -> None:
        new_topics = [
            NewTopic(topic=topic_name, num_partitions=1, replication_factor=1)
        ]
        try:
            create_topic_futures_dict: dict[str, Future] = admin_client.create_topics(
                new_topics
            )
        except KafkaException as err:
            print("Failed to create topic")
            pytest.fail(f"Failed to create topic: {err}")

        # Strategy 1: Use as_completed, to wait for all futures to finish
        # for _ in as_completed(futures_dict.values()):
        #     pass

        # Strategy 2: Use future.result() to block the main thread till each completes
        # Strategy 2 is better, as it allows us to log which topic completed and failed
        for topic, future in create_topic_futures_dict.items():
            try:
                result = future.result()
                print(f"Topic '{topic}' created successfully with result: {result}")
            except Exception as e:
                print(f"Failed to create topic '{topic}': {e}")
                pytest.fail(f"Failed to create topic: {topic}")

    def block_till_data_published_to_topic():
        """
        Responsible for polling the topic to be sure the produced test record is ready
        before the integration test
        """
        consumer = Consumer(
            {
                "bootstrap.servers": "localhost:29092",
                "group.id": f"test-group-{uuid.uuid4()}",
                "auto.offset.reset": "earliest",
            }
        )
        consumer.subscribe([topic_name])
        msg = consumer.poll(timeout=30)
        if msg is None:
            print("Failed to get message after waiting for 30 seconds")
            pytest.fail("Failed to get message after waiting for 30 seconds")
        else:
            print(f"Received message: {msg.value()}")

    def add_records_to_topic() -> None:
        def on_delivery_callback(
            kafka_error: KafkaError | None, record: Record
        ) -> None:
            if kafka_error:
                print(f"Failed to publish test record to topic: {record}")
                pytest.fail(f"Failed to publish test record to topic: {record}")

        serialized_value: str = json.dumps(
            [single_record.model_dump() for single_record in dummy_records]
        )
        producer.produce(
            topic=topic_name, value=serialized_value, on_delivery=on_delivery_callback
        )
        producer.flush()
        # confirm data exists in topic with a separate test consumer; poll till get data
        block_till_data_published_to_topic()

    def drop_topic() -> None:
        try:
            drop_topic_futures_dict: dict[str, Future] = admin_client.delete_topics(
                [topic_name]
            )
        except KafkaException as err:
            pytest.fail(f"Failed to delete topic: {err}")

        # Strategy 2: Use future.result() to block the main thread till each completes
        # Strategy 2 is better, as it allows us to log which topic completed and failed
        for topic, future in drop_topic_futures_dict.items():
            try:
                future.result()
                print(f"Topic '{topic}' deleted successfully")
            except Exception as e:
                print(f"Failed to delete topic '{topic}': {e}")
                pytest.fail(f"Failed to create topic: {topic}")

    try:
        create_topic()
        add_records_to_topic()
        yield
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        drop_topic()


@pytest.fixture
def generic_consumer(topic_name: str) -> GenericConsumer[RawSearchTermsRecord]:
    print(f"Generic Consumer subscribing to: {topic_name}")
    return GenericConsumer(
        consumer_config={
            "bootstrap.servers": "localhost:29092",
            "enable.auto.commit": False,
            "client.id": f"rt-yse-search-consumer-test-1-{uuid.uuid4()}",
            "group.id": f"rt-yse-search-consumer-test-1-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
        },
        topic_name=topic_name,
        model=RawSearchTermsRecord,
    )


class TestGenericConsumer:
    def test_consume(
        self,
        setup_and_teardown_test_consume,
        generic_consumer: GenericConsumer[RawSearchTermsRecord],
        dummy_records: list[RawSearchTermsRecord],
    ) -> None:
        """
        GenericConsumer
        - consumer_config
        - topic_name
        - model

        Test def consume
        - Confluent Kafka consumer should return back messages
        - Raw message should be deserialized into pydantic base model

        Act
        - call consume

        Assert
        - We get one record
        """
        time.sleep(3)
        # IF we have a topic with 1 message inside + a generic consumer using RawSearchTermsRecord
        # WHEN i call generic_consumer.consume()
        consumed_records: list[RawSearchTermsRecord] = generic_consumer.consume()
        # THEN i expect, to get the message, deserialized into a RawSearchTermsRecord
        assert consumed_records == dummy_records
