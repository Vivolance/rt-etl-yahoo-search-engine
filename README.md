# RT ETL Pipeline for Extracting Structured Data from Yahoo Search HTML

## Objective:

Provides a robust web-server which extracts structured data from yahoo search results

As the process of extracting structured data is CPU intensive and slow

We propose an architecture which ingests these yahoo search results async

## Business Requirements

1. Provide an async API, allowing users to pass in a search term. They will be given a job id, to check the status of the extraction, and retrieve the results.

2. The async API should support high-throughput and real-time extraction in order of seconds.
- Users should be able to receive back the results in seconds
- The async server should be able to handle ~1,000+ concurrent connections

## High-Level Architecture

![high-level-architecture.png](./images/high-level-architecture.png)

## Key Design Decisions

1. Async server as the front-desk.
- Responsible for receiving search term + creating a unique job id
- Saves search term + customer id + job id + status of job into Postgres
- Expose three endpoints
  - One to create a job
  - One to check status of job
  - One to get results of job
- Delegates extraction to consumer / producer process by producing to Kafka topic

2. Kafka Broker
- Contains two topic: `raw_search_terms` and `raw_search_results`
  - search_term: str
  - customer_id: str
  - job_id: str
  - created_at: datetime
- This topic will be ingested by the consumer / producer process

3. Yahoo Search Consumer / Producer
- Responsible for making an API call to yahoo search engine with the search term
- Saves the raw search results into Postgres
- Produces to `raw_search_results` topic
  - search_term: str
  - customer_id: str
  - job_id: str
  - search_result_id: id
  - created_at: datetime

4. Extractor Consumer / Producer
- Responsible for extracting the search result from postgres
- Extracts the structured data from the result
- Saves the structured data into postgres table
- Updates the job status to completed for the job_id

## Project Setup

### 1. Setup env

```commandline
poetry shell
poetry install
```

### 2. Run Zookeeper Server

Navigate to kafka folder

```commandline
bin/zookeeper-server-start.sh ./config/zookeeper.properties
```

### 3. Run Kafka Server

```commandline
bin/kafka-server-start.sh ./config/server.properties
```

### 4. Create two topics:

```
./create_topics.sh
```

Topic 1: `raw_search_terms`

```json
{
  "user_id": "123",
  "search_term": "Starbucks Coffee",
  "job_id": "123",
  "job_created_at": "2024-09-21 00:00:00"
}
```

Topic 2: `raw_search_results`

```json
{
  "user_id": "123",
  "search_term": "Starbucks Coffee",
  "job_id": "123",
  "job_created_at": "2024-09-21 00:00:00", 
  "raw_search_results_id": "1234",
  "raw_search_at": "2024-09-21 00:00:01"
}
```

## Producing a message

### Spin up server

```commandline
export PYTHONPATH=.
python3 src/app.py
```

### POST command to `localhost:8000` with payload

POST http://localhost:8000/search

```json
{
	"search_term": "Chicken Rice",
	"user_id": "1"
}
```

Response

```
{
	"job_id": "7cd25644-9468-4b99-a60b-9ea25513eb1d",
	"search_term": "Chicken Rice"
}
```

### Run Yahoo Search Process

```commandline
python src/yahoo_search_process.py
```

## Check topic: `raw_search_terms`

```commandline
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw_search_terms --from-beginning

["{\"user_id\": \"1\", \"search_term\": \"Coffee Bean\", \"job_id\": \"f2dac9d8-d840-404d-b868-568a2615aa03\", \"job_created_at\": \"2024-09-21T08:28:49\"}"]
```

## Check topic: `raw_search_results`

```commandline
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic raw_search_results --from-beginning

[{"user_id": "1", "search_term": "Gout", "job_id": "f59200ad-50dc-46c8-8287-2c85ac25e9b1", "job_created_at": "2024-09-22T09:43:41", "raw_search_results_id": "28e9741b-d51b-4076-8153-46e48febccf5", "raw_search_at": "2024-09-22T10:14:39"}, {"user_id": "1", "search_term": "Gout", "job_id": "1831cdc1-d555-4292-bf52-f6143ce0a9dd", "job_created_at": "2024-09-22T09:43:42", "raw_search_results_id": "7ebb9571-8e17-46f3-9082-ec32c96051d0", "raw_search_at": "2024-09-22T10:14:39"}, {"user_id": "1", "search_term": "Mala", "job_id": "da93d5f9-3ef8-4808-9d1e-b177a69e1bb5", "job_created_at": "2024-09-22T10:14:39", "raw_search_results_id": "1e7fc34d-9bc3-46a1-ab4d-c361b5cb259e", "raw_search_at": "2024-09-22T10:14:39"}]
[{"user_id": "1", "search_term": "Chicken Rice", "job_id": "7cd25644-9468-4b99-a60b-9ea25513eb1d", "job_created_at": "2024-09-22T10:14:56", "raw_search_results_id": "fadc5f38-fd6b-469a-8ced-91225cf97267", "raw_search_at": "2024-09-22T10:14:57"}]
```

## TODO:
- [x] Create Async front desk server, responsible for giving a job id to the client
- [x] Create alembic sqlalchemy tables
- [ ] Added `/search` endpoint 
  - [x] to save a new record to `jobs` table
  - [ ] Make main thread put a record to be produced, to `queue.Queue`
  - [ ] Create background thread to listen to messages from a `queue.Queue`, to be produced to topic `raw_search_terms`
  - [ ] Setup Kafka Cluster, create new topic `raw_search_terms`
- [ ] Add first consumer / producer process. `yahoo_search_consumer_producer.py`
  - [ ] Consumes from `raw_search_terms`
  - [ ] Makes API call to yahoo search engine API
  - [ ] Save results to `raw_search_results` table
  - [ ] Produce message to `raw_search_results` topic
- [ ] Add second consumer process. `extractor_consumer.py`
  - [ ] Consumes from `raw_search_results` topic
  - [ ] Use `raw_search_results_id` to query for full search results from `raw_search_results` PG table
  - [ ] Extract
  - [ ] Save results to `extracted_search_results` PG table
  - [ ] Update SET `jobs` record's `job_status` to `JobStatus.COMPLETED`