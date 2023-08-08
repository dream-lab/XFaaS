import time
import logging as logger

from python.src.utils.classes.commons.serwo_objects import SerWOObject

logger.debug('This is a debug message')
logger.info('This is an info message')
logger.warning('This is a warning message')
logger.error('This is an error message')
logger.critical('This is a critical message')
logger.basicConfig(level=logger.DEBUG)


def function(serwoObject) -> SerWOObject:
    logger.info("Enter function 1")
    start_time = time.time()*100
    time.sleep(2)
    end_time = time.time()*100
    logger.info(f"Sleep executed for - {(end_time - start_time)/1000} seconds")
    return SerWOObject(body={"message": "Function executed"})
