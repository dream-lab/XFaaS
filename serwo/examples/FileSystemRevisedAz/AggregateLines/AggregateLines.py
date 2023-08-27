# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject
def user_function(serwo_list_object):
    try:
        objects= serwo_list_object.get_objects()
        strings = []
        numIters = 0
        for obj in objects:
            body = obj.get_body()
            strings = body["sortedText"]
            numIters = body["numIters"]
            st = []
            for text in strings:
                st.append(text)
            c = ''.join(st)
            strings.append(c)
        returnbody = {"text":strings,
                      "numIters":numIters}
        return SerWOObject(body = returnbody)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
