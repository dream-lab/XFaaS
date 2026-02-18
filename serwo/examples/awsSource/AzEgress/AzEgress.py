from python.src.utils.classes.commons.serwo_objects import SerWOObject
import requests
def user_function(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        metadata = serwoObject.get_metadata()
        s = SerWOObject(body=body)
        inp = dict(body=body,metadata=metadata)
        url = 'https://xfaasAzSink713547.azurewebsites.net/api/orchestrators/Orchestrate'
        ## call sink function

        resp = requests.post(url,json=inp)
        return s
    except Exception as e:
        print('in egress: ',e)
        return None