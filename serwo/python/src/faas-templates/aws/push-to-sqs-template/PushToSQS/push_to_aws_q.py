import boto3
import json
import time
import botocore.session
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import logging
import uuid

# Create SQS client
"""
!!!!!!!!!! IMPORTANT !!!!!!!!!
NOTE - Currently the access_key_id = , secret_access_key =  are HARDCODED. WE NEED TO TEMPLATE THIS
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""
AWS_ACCESS_KEY_ID = "{{access_key_id}}"
AWS_SECRET_ACCESS_KEY = "{{secret_access_key}}"
sqs = boto3.client(
    "sqs",
    region_name="ap-south-1",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

AWS_MESSAGE_THRESHOLD = 256 * 1024

queue_url = "{{queue_url}}"

def generate_s3_key(prefix="xfaas", extension="json"):
    """
    Generate a unique S3 object key with the given prefix and extension.
    """
    if prefix == None:
        prefix = "xfaas"
    return f"{prefix}/{uuid.uuid4()}.{extension}"

def upload_json_payload(bucket, payload, prefix="xfaas"):
    """
    Serializes and uploads the payload (dict/list) to the given S3 bucket.
    Returns the key used.
    """
    key = generate_s3_key(prefix=prefix, extension="json")
    s3 = boto3.client(
        "s3",
        region_name="ap-south-1",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )
    data_bytes = json.dumps(payload).encode("utf-8")
    s3.put_object(Bucket=bucket, Key=key, Body=data_bytes)
    return key


# Send message to SQS queue
def user_function(serwoObject) -> SerWOObject:
    try:
        message = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        message["body"] = data
        message["metadata"] = metadata
        #logging.info(f"Input {message}")
        if "aws" not in message["body"]:
            logging.info("AWS details for long message is not present in function body")

        output_bytes = json.dumps(message).encode("utf-8")
        if len(output_bytes) > AWS_MESSAGE_THRESHOLD:
            user_bucket = None
            # If output is large (autotrigger)
            event_body = message["body"]
            if isinstance(event_body, dict):
                if "aws" in event_body:
                    aws_details = event_body.get("aws", {})
                    user_bucket = aws_details.get("bucket")
            if not user_bucket:
                raise ValueError("This workflow needs long payload size handling. Please provide valid storage details for each CSP in the event")
            # --- Proceed to upload ---
            deployment_id = metadata.get("deployment_id")
            key = upload_json_payload(user_bucket, message["body"], prefix= deployment_id)
            result = {
                
                "large_payload": 1,
                "aws": {
                    "bucket": user_bucket,
                    "key": key
                }
            }

            message["body"] = result

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
