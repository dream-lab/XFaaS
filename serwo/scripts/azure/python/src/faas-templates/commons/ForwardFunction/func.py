from python.src.utils.classes.commons.serwo_objects import SerWOObject


def function(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        return SerWOObject(body=body)
    except Exception as e:
        return SerWOObject(error=True)
