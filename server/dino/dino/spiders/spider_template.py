import os
import json
import boto3
from dotenv import load_dotenv
from scrapy import Spider, Request
from math import ceil
from confluent_kafka import Producer
import time

# Instructions for integrating with FastAPI
# ----------------------------------------
# 1. Import this spider into your FastAPI application's main.py file.
# 2. Use the Scrapy CrawlerProcess to run the spider.
# 3. Define an endpoint in your FastAPI application that triggers the spider.
# 4. Call the spider using its name ('custom_scraper' in this case) when the endpoint is hit.
# Replace 'YOUR_START_URL_HERE', 'YOUR_CSS_SELECTOR_HERE', 'YOUR_BUCKET_NAME', and 'YOUR_FOLDER_NAME' with actual values.


# Load environment variables from .env file
load_dotenv()
conf = {'bootstrap.servers':os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'client.id': 'spider-producer-n'}
producer = Producer(conf)
class CustomScraper(Spider):
    name = 'custom_scraper'
    start_urls = ['YOUR_START_URL_HERE'] # Define your start URLs here
    output_file = 'custom_output.json' # Output file name
    bucket_name = 'YOUR_BUCKET_NAME' # S3 bucket name
    folder_name = 'YOUR_FOLDER_NAME' # S3 folder name

    def parse(self, response):
        # Custom parsing logic goes here
        # Example: Extract links from the page
        links = response.css('YOUR_CSS_SELECTOR_HERE').extract()

        for link in links:
            # Customize the request to the extracted links
            yield Request(link, callback=self.custom_parse_method)

    def custom_parse_method(self, response):
        # Custom parsing logic for each extracted link
        # Example: Extract product details
        product_data = {
            'title': response.css('YOUR_CSS_SELECTOR_HERE').get(),
            'description': response.css('YOUR_CSS_SELECTOR_HERE').get(),
            # Add more fields as needed
        }

        # Custom processing or storage logic
        # Example: Save product data to a file or database
        # Convert product_data to a JSON string
        json_str = json.dumps(product_data)

        # Send the JSON string to the Kafka topic
        producer.produce(self.folder_name, value=json_str.encode('utf-8'))
        producer.flush()  # Ensure the message is delivered
        print(product_data)
        print("Message sent")
       

    

    def closed(self, reason):
        producer.flush()
        producer.close()
        try:
            s3 = boto3.client('s3',
                            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                            region_name=os.getenv('AWS_REGION'))
            # Ensure logs.txt exists and is updated regardless of the reason for closure
            logs_file = f'{self.folder_name}/logs.txt'
            if not s3.head_object(Bucket=self.bucket_name, Key=logs_file):
                s3.put_object(Bucket=self.bucket_name, Key=logs_file, Body='')
            else:
                # Download the current content of logs.txt
                s3.download_file(self.bucket_name, logs_file, 'temp_logs.txt')
                with open('temp_logs.txt', 'r') as temp_logs_file:
                    current_logs = temp_logs_file.read()

            # Log success or error message based on the reason
            if reason == 'finished':
                log_message = f"{self.name} finished successfully.\n"
            else:
                log_message = f"{self.name} closed with reason: {reason}\n"

            # Append the new log message to the current logs
            updated_logs = current_logs + log_message

            # Upload the updated logs back to S3
            s3.put_object(Bucket=self.bucket_name, Key=logs_file, Body=updated_logs, ContentType='text/plain', ACL='public-read')

        except Exception as e:
            # Log the error to logs.txt
            error_message = f"Error in {self.name}: {str(e)}\n"
            s3.put_object(Bucket=self.bucket_name, Key=logs_file, Body=error_message, ContentType='text/plain', ACL='public-read')
            self.logger.error(f"Error in {self.name}: {str(e)}")

#Extracting a Particular Tag
# # To extract a particular tag, use the `css` or `xpath` method on the response object.
# # For example, to extract all <p> tags from the page:
# paragraphs = response.css('p').getall()

# # Or, to extract the text of the first <p> tag:
# first_paragraph = response.css('p').get()

# # To extract an attribute of a tag, use the `::attr(attribute_name)` syntax.
# # For example, to extract the href attribute of all <a> tags:
# links = response.css('a::attr(href)').getall()
            
##################################################################################################################
#Using Callbacks
# To use a callback, specify it in the Request object. The callback is a method that will be called with the response of the request.
# For example, to make a request to a link and process the response with a custom method:
# yield Request(link, callback=self.custom_parse_method)

# # In the custom method, you can extract data, make further requests, or perform any other processing.
# def custom_parse_method(self, response):
#     # Custom parsing logic here
#     pass
  
# ##################################################################################################################
#  Passing Data to meta   
# To pass data to the `meta` attribute of a Request, simply include it in the Request object.
# This is useful for passing data that needs to be available in the callback method.
# # For example, to pass a product ID to a callback method:
# yield Request(link, callback=self.custom_parse_method, meta={'product_id': product_id})

# # In the callback method, you can access the data passed in `meta` like this:
# def custom_parse_method(self, response):
#     product_id = response.meta['product_id']
#     # Now you can use product_id in your parsing logic
# ################################################################################################################## 
            


