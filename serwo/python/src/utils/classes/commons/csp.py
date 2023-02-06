from enum import Enum

class CSP(Enum):
    AWS = 1
    AZURE = 2

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
