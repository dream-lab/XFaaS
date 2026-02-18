from python.src.utils.classes.commons.serwo_objects import SerWOObject
import requests
import json
def user_function(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        s = SerWOObject(body=body)
        inp = dict(body=body,metadata=metadata)
        url = 'https://dr4bi3nlte.execute-api.ap-south-1.amazonaws.com/serwo/execute'
        inp = {"input":json.dumps(inp) , "stateMachineArn":"arn:aws:states:ap-south-1:235319806087:stateMachine:AwsSink-8b0WSxcrLzRu"}
        ## call sink function

        resp = requests.post(url,json=inp)
        return s
    except Exception as e:
        print('in egress: ',e)
        return None