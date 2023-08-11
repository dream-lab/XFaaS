import boto3
import json
import time
import botocore.session
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging

# Create SQS client
"""
!!!!!!!!!! IMPORTANT !!!!!!!!!
NOTE - Currently the access_key_id = , secret_access_key =  are HARDCODED. WE NEED TO TEMPLATE THIS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

sqs = boto3.client(
    "sqs",
    region_name="ap-south-1",
    aws_access_key_id="{{access_key_id}}",
    aws_secret_access_key="{{secret_access_key}}",
)


queue_url = "{{queue_url}}"


# Send message to SQS queue
def function(serwoObject) -> SerWOObject:
    try:
        message = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        message["body"] = data
        message["metadata"] = metadata
        logging.info(f"Input {message}")
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message),
            MessageDeduplicationId=f"serwo-{int(time.time()*1000)}",
            MessageGroupId="serwo",
        )
        print(
            f"MessageID::{response['MessageId']},AWSSQSQueue::{queue_url}, Timestamp::{int(time.time()*1000)}"
        )
        return SerWOObject(body=data)
    except Exception as e:
        logging.info(f"Excep {e}")
        return SerWOObject(error=True)
