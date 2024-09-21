echo "Dropping raw_search_terms topic"
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-topics.sh kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw_search_terms
echo "Creating raw_search_terms topic"
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-topics.sh --create --topic raw_search_terms --bootstrap-server localhost:9092 --partitions 10 --replication-factor 1
echo "Dropping raw_search_terms topic"
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-topics.sh kafka-topics.sh --bootstrap-server localhost:9092 --delete --topic raw_search_results
echo "Creating raw_search_results topic"
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-topics.sh --create --topic raw_search_results --bootstrap-server localhost:9092 --partitions 10 --replication-factor 1
echo "Listing all topics:"
/Users/elsonchan/Desktop/kafka_2.13-3.7.1/bin/kafka-topics.sh --list --bootstrap-server localhost:9092