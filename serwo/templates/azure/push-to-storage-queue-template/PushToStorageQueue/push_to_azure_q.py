from azure.storage.queue import QueueService, QueueMessageFormat
from azure.storage.blob import BlobServiceClient
import json
from python.src.utils.classes.commons.serwo_objects import SerWOObject
import os, uuid
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta, timezone
from azure.core.exceptions import ResourceExistsError

connect_str = "{{connection_string}}"
queue_service = QueueService(connection_string=connect_str)
queue_name = "{{queue_name}}"
# Setup Base64 encoding and decoding functions
queue_service.encode_function = QueueMessageFormat.binary_base64encode
queue_service.decode_function = QueueMessageFormat.binary_base64decode

MAX_QUEUE_MSG_SIZE = 64 * 1024

def parse_connection_string(conn_str):
    tokens = dict(x.split('=', 1) for x in conn_str.strip().split(';') if '=' in x)
    #tokens is a dict with all the values in the connections string like DefaultEndpointsProtocol, AccountName, AccountKey, BlobEndpoint, .. etc
    account_name = tokens.get('AccountName')
    account_key = tokens.get('AccountKey')
    return account_name, account_key

def upload_to_blob(payload, container):
    blob_service = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service.get_container_client(container)
    if not container_client.exists():
        try:
            container_client.create_container()
        except ResourceExistsError:
            print("Container already exists, probably due to a parallel workflow")
            pass
        blob_name = f"{uuid.uuid4()}.json"
    blob_client = blob_service.get_blob_client(container=container, blob=blob_name)
    data_bytes = json.dumps(payload).encode("utf-8")
    blob_client.upload_blob(data_bytes, overwrite=True)
    return blob_name


def user_function(serwoObject) -> SerWOObject:
    try:
        fin_dict = dict()
        data = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        fin_dict["body"]  = data
        fin_dict["metadata"] = metadata
        #TODO: 
        if len(json.dumps(fin_dict).encode("utf-8")) > MAX_QUEUE_MSG_SIZE:
            blob_details = data.get(data.get("csp"))
            container_name = blob_details.get("container") if isinstance(blob_details, dict) else None
            if not container_name:
                container_name = "xfaas-large-payload-container"

            blob_name = upload_to_blob(fin_dict, container_name)

            account_name, account_key = parse_connection_string(connect_str)
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            blob_url_with_sas = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"

            

            payload_data = {
            
                "large_payload": 1,
                "azure": {
                    "container": container_name,
                    "blob_name": blob_name,
                    "blob_url": blob_url_with_sas
                    
                }
            }
            queue_service.put_message(queue_name, json.dumps(payload_data).encode("utf-8"))
            
            
        else: 
            queue_service.put_message(queue_name, json.dumps(fin_dict).encode("utf-8"))
        return SerWOObject(body=data)
    except Exception as e:
        print(e)
        return SerWOObject(error=True)
