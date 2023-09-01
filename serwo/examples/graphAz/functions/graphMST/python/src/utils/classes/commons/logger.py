import logging


class LoggerFactory(object):

    _LOG = None

    @staticmethod
    def __create_logger(log_file,  log_level):
        """
        A private method that interacts with the python
        logging module
        """
        # set the logging format
        log_format = "XFaaS::%(asctime)s:%(levelname)s:%(message)s"
        
        # Initialize the class variable with logger object
        LoggerFactory._LOG = logging.getLogger(log_file)
        logging.basicConfig(level=logging.INFO, format=log_format, datefmt="%Y-%m-%d %H:%M:%S")
        
        # set the logging level based on the user selection
        if log_level == "INFO":
            LoggerFactory._LOG.setLevel(logging.INFO)
        elif log_level == "ERROR":
            LoggerFactory._LOG.setLevel(logging.ERROR)
        elif log_level == "DEBUG":
            LoggerFactory._LOG.setLevel(logging.DEBUG)
        return LoggerFactory._LOG

    @staticmethod
    def get_logger(log_file, log_level):
        """
        A static method called by other modules to initialize logger in
        their own module
        """
        logger = LoggerFactory.__create_logger(log_file, log_level)
        
        # return the logger object
        return logger