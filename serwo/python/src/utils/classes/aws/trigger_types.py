from enum import Enum


class TriggerType(Enum):
    AWS_API_GATEWAY = (1,)
    AWS_SQS = 2

    @classmethod
    def get_trigger_type(cls, string):
        if string == "rest" or string == "REST":
            return TriggerType.AWS_API_GATEWAY
        elif string == "sqs" or string == "SQS":
            return TriggerType.AWS_SQS
