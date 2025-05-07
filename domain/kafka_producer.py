"""Kafka producer implementations."""
import json
import logging
import uuid
from datetime import datetime
import ssl

from kafka import KafkaProducer
from kafka.errors import KafkaError

from settings import KAFKA_BOOTSTRAP_SERVERS, USE_KAFKA_SASL_AUTH, \
    KAFKA_USERNAME, KAFKA_PASSWORD


def publish_message(
        name,
        topic,
        payload=None,
        type_message_key=None,
        metadata=None,
):
    """Post a new post in the Kafka topic."""
    try:
        logging.info(f"Publishing message {name} in {topic}")
        protocol = {
            "name": name,
            "version": 1.0,
            "flow_id": str(uuid.uuid5(
                uuid.NAMESPACE_X500, datetime.now().isoformat())),
            "payload": payload,
            "metadata": metadata,
        }
        if type_message_key:
            protocol['metadata'] = {"type_message_key": type_message_key}

        kafka_config = {
            "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS,
            "security_protocol": "SASL_SSL",
            "ssl_context": ssl.create_default_context(),
            "sasl_mechanism": "PLAIN",
            "sasl_plain_username": KAFKA_USERNAME,
            "sasl_plain_password": KAFKA_PASSWORD
        } if USE_KAFKA_SASL_AUTH else {
            "bootstrap_servers": KAFKA_BOOTSTRAP_SERVERS
        }

        producer_instance = KafkaProducer(**kafka_config)

        producer_instance.send(topic, bytes(json.dumps(protocol), "utf-8"))
        producer_instance.flush()
        producer_instance.close()

    except KafkaError as e:
        logging.exception(f"Error publishing message {name} - {type(e)} {e}")
