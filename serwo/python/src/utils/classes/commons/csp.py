from enum import Enum


class CSP(Enum):
    AWS = 1
    AZURE = 2

    # TODO - add a CSP id which is a combination of the CSP name and the region
    # for unique identification of the region.

    @staticmethod
    def build_resources():
        pass

    @staticmethod
    def build_workflow():
        pass

    @staticmethod
    def deploy_workflow():
        pass

    @staticmethod
    def toCSP(csp: str):
        if csp.lower() == "aws":
            return CSP.AWS
        elif csp.lower() == "azure":
            return CSP.AZURE

    @staticmethod
    def toString(csp):
        if csp == CSP.AWS:
            return "aws"
        if csp == CSP.AZURE:
            return "azure"
