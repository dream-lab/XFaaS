from python.src.utils.classes.commons.serwo_objects import SerWOObject

def user_function(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        size_in_kb = body['size_in_kb']
        ## geneerate string of size_in_kb with random data
        data = 'a' * size_in_kb
        s = SerWOObject(body={'data': data})
        return s
    except Exception as e:
        print('in iostress: ',e)
        return None