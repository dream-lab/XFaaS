from python.src.utils.classes.commons.serwo_objects import SerWOObject


def user_function(serwo_list_object) -> SerWOObject:
    try:
        objects = serwo_list_object.get_objects()
        print(objects)
        returnbody = {}
        for obj in objects:
            body = obj.get_body()
            for key in body:
                returnbody[key] = body[key]
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")