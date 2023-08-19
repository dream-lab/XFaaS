import os
import json

from python.src.utils.classes.commons.logger import LoggerFactory

logger = LoggerFactory.get_logger(__file__, log_level="INFO")

if __name__ == "__main__":
    logger.info("Listing all clouformation Stacks and placing them in xfaas-all-stacks.json")
    os.system("aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE > xfaas-all-stacks.json")

    with open("xfaas-all-stacks.json", "r") as file:
        contents = file.read()
        allstacks = json.loads(contents)
        
        stackinfo = allstacks['StackSummaries']
        if stackinfo:
            for stack in stackinfo:
                stackname = stack['StackName']
                os.system(f"aws cloudformation delete-stack --stack-name {stackname}")
                logger.info(f"Deleting Stack {stackname}")
        else:
            logger.info(f"No available stacks to delete")

    logger.info("Deleting the xfaas-all-stacks.json containing stack information")
    os.system("rm -r xfaas-all-stacks.json")
