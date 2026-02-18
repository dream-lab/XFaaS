from python.src.utils.classes.commons.serwo_objects import SerWOObject
from urllib.request import urlopen
from datetime import datetime
from time import mktime


def user_function(serwoObject) -> SerWOObject:
    try:
        res = urlopen('http://just-the-time.appspot.com/')
        result = res.read().strip()
        result_str = result.decode('utf-8')
        ntp_time = int(mktime(datetime.strptime(result_str, "%Y-%m-%d %H:%M:%S").timetuple()))
        ntp_source = serwoObject.get_body()['ntp_time_source'] 
        data = {'data':'String Received from Source','ntp_time':ntp_time,'ntp_time_source':ntp_source}
        

        return SerWOObject(body=data)
    except Exception as e:
        print('in iostress: ',e)
        return None