from confluent_kafka import Consumer, KafkaError
import boto3
import os
import json
import uuid
import time

# Kafka consumer configuration
conf = {'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'), 'group.id': 'spider-consumer'}
consumer = Consumer(conf)

# Subscribe to topics
topics = ['softwareadvice', 'softwaresuggest','producthunt','crozdesk']  # Add your additional topics here
consumer.subscribe(topics)

# Initialize S3 client using environment variables
s3 = boto3.client('s3',
                  aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                  aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                  region_name=os.getenv('AWS_REGION'))

# Specify the S3 bucket
bucket_name = 'dinostomach'

# Consume messages
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            time.sleep(1)
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
        
        # Get topic name
        topic = msg.topic()
        
        # Get message value (assuming it's a JSON string)
        message_value = msg.value().decode('utf-8')
        print(f"Received message from topic {topic}: {message_value}")

        # Parse JSON string into a dictionary
        json_data = json.loads(message_value)
        
        # Generate a unique file name (UUID)
        file_name = f"{uuid.uuid4()}.json"
        
        # Create folder name based on topic
        folder_name = topic
        
        # Put the JSON data into a file and upload it to S3
        s3.put_object(Bucket=bucket_name, Key=f"{folder_name}/{file_name}", Body=json.dumps(json_data))
        print(f"Message saved to S3: {folder_name}/{file_name}")
except KeyboardInterrupt:
    pass
finally:
    # Close consumer
    consumer.close()
