import json
import uuid
from asyncio import Future
from datetime import datetime
from typing import Generator

import pytest
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import Consumer, KafkaException

from src.consumers.producers import AbstractProducer
from src.models.kafka_records_data_classes.raw_search_terms import RawSearchTermsRecord


# Create a mock consumer
@pytest.fixture
def consumer(topic_name: str) -> Consumer:
    """Kafka consumer fixture."""
    consumer_config = {
        "bootstrap.servers": "localhost:29092",
        "group.id": f"test_group_{uuid.uuid4()}",
        "auto.offset.reset": "earliest",
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe([topic_name])
    yield consumer
    consumer.close()


# Create a Kafka Admin client to handle Kafka resources
@pytest.fixture
def admin_client() -> AdminClient:
    return AdminClient({"bootstrap.servers": "localhost:29092"})


# Create a random topic name
@pytest.fixture()
def topic_name() -> str:
    return f"raw_search_terms_{uuid.uuid4()}"


# Create dummy record for testing
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


# To set up and tear down the Kafka topic for testing
@pytest.fixture
def setup_and_teardown_test_produce(
    admin_client: AdminClient,
    topic_name: str,
) -> Generator[None, None, None]:

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
        for topic, future in create_topic_futures_dict.items():
            try:
                future.result()
                print(f"Topic '{topic}' created successfully")
            except Exception as e:
                print(f"Failed to create topic '{topic}': {e}")
                pytest.fail(f"Failed to create topic '{topic_name}': {e}")

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
        yield
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        drop_topic()


@pytest.fixture
def abstract_producer(topic_name: str) -> AbstractProducer[RawSearchTermsRecord]:
    return AbstractProducer(
        producer_config={
            "bootstrap.servers": "localhost:29092",
            "client.id": f"rt-yse-search-producer-test-{uuid.uuid4()}",
        },
        topic_name=topic_name,
    )


class TestAbstractProducer:
    """
    AbstractProducer
    - producer_config
    - topic_name

    Test def produce
    - Abstract Producer class should be able to serialize basemodel
    and produce to topic

    Prepare:
    - Create a topic
    - "raw_search_term_uuid.uuid4()"
    - Create a mock consumer to consume
    - Admin Client Setup Kafka resources

    Act:
    - Call produce method for Abstract Producer

    Assert:
    - Mock Consumer should consume from topic and deserialize back to Dataclass
    - Consume records == dummy_records

    Tear Down:
    - Admin Client to teardown kafka resources
    - Drop Topic created
    """

    def test_produce(
        self,
        setup_and_teardown_test_produce,
        abstract_producer: AbstractProducer[RawSearchTermsRecord],
        dummy_records: list[RawSearchTermsRecord],
        consumer: Consumer,
    ) -> None:

        abstract_producer.produce(dummy_records)
        abstract_producer.flush_producer()

        msg = consumer.poll(timeout=30)
        if msg is None:
            print("Failed to get message after waiting for 30 seconds")
        else:
            print(f"Received message: {msg.value()}")

        # deserialize the message
        consumed_value = json.loads(msg.value())
        consumed_records = [
            RawSearchTermsRecord.model_validate(record) for record in consumed_value
        ]

        assert consumed_records == dummy_records
