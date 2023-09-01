# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def user_function(xfaas_object):
    try:
        print("Inside user function : Aggregator")
        results = []

        for idx, item in enumerate(xfaas_object.get_objects()):
            body = item.get_body()
            results.append(body)
        predictions = {"Predictions": results}
        return SerWOObject(body=predictions)

    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
