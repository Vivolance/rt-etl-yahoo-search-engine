#!/bin/bash

# Wait for Kafka to be ready
until /opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --list; do
  echo "Waiting for Kafka to be ready..."
  sleep 5
done

# Drop and create raw_search_terms topic
echo "Dropping raw_search_terms topic"
/opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic raw_search_terms

echo "Creating raw_search_terms topic"
/opt/bitnami/kafka/bin/kafka-topics.sh --create --topic raw_search_terms --bootstrap-server kafka:9092 --partitions 10 --replication-factor 1

# Drop and create raw_search_results topic
echo "Dropping raw_search_results topic"
/opt/bitnami/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --delete --topic raw_search_results

echo "Creating raw_search_results topic"
/opt/bitnami/kafka/bin/kafka-topics.sh --create --topic raw_search_results --bootstrap-server kafka:9092 --partitions 10 --replication-factor 1

# List all topics
echo "Listing all topics:"
/opt/bitnami/kafka/bin/kafka-topics.sh --list --bootstrap-server kafka:9092
