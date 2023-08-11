import os
import logging as logger
import boto3
from botocore.exceptions import ClientError

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
logger.basicConfig(level=logger.DEBUG)


class ObjectWrapper:
    """Encapsulates S3 object actions."""

    def __init__(self, s3_object):
        """
        :param s3_object: A Boto3 Object resource. This is a high-level resource in Boto3
                          that wraps object actions in a class-like structure.
        """
        self.object = s3_object
        self.key = self.object.key

    def put(self, data):
        """
        Upload data to the object.

        :param data: The data to upload. This can either be bytes or a string. When this
                     argument is a string, it is interpreted as a file name, which is
                     opened in read bytes mode.
        """
        put_data = data
        if isinstance(data, str):
            try:
                put_data = open(data, "rb")
            except IOError:
                logger.exception("Expected file name or binary data, got '%s'.", data)
                raise

        try:
            self.object.put(Body=put_data)
            self.object.wait_until_exists()
            logger.info(
                "Put object '%s' to bucket '%s'.",
                self.object.key,
                self.object.bucket_name,
            )
        except ClientError:
            logger.exception(
                "Couldn't put object '%s' to bucket '%s'.",
                self.object.key,
                self.object.bucket_name,
            )
            raise
        finally:
            if getattr(put_data, "close", None):
                put_data.close()


def get_payload(bucket_name, object_name, file_name):
    """
    Download the zip upload from the s3 bucket and unzip here
    """
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, object_name, file_name)
    os.system(f"unzip {file_name} /payload/")


def put_payload(bucket_name, object_name, file_name):
    """
    Upload the zip upload from the s3 bucket and unzip here
    """
    os.system(f"zip -r /payload/ /out/{file_name}")
    s3 = boto3.client("s3")
    s3.upload_file(bucket_name, object_name, file_name)
    pass


def build():
    # include the serwo code for this.
    pass


def deploy():
    pass


def handle(event_type):
    if event_type == "XFAAS_BUILD":
        build()
    if event_type == "XFAAS_DEPLOY":
        deploy()


def handler(event, context):
    """
    Based on the event type of the workflow.
    The deployment handler calls the appropriate function
    """
    event_type = event["body"]["event_type"]
    handle(event_type)
    pass


# 2 base container images.
def main():
    pass
