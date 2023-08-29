import json
import nltk
nltk.download('punkt')
from textblob import TextBlob
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def handle(req):
    """
    Calculate the polarity and subjectivity of the given set of comments.

    Args:
        req (str): The input text containing comments.

    Returns:
        str: A JSON string containing the calculated polarity, subjectivity, and other metrics.
    """
    blob = TextBlob(req)
    res = {
        "polarity": 0,
        "subjectivity": 0
    }

    for sentence in blob.sentences:
        res["subjectivity"] = res["subjectivity"] + sentence.sentiment.subjectivity
        res["polarity"] = res["polarity"] + sentence.sentiment.polarity

    total = len(blob.sentences)

    res["sentence_count"] = total
    res["polarity"] = res["polarity"] / total
    res["subjectivity"] = res["subjectivity"] / total

    return json.dumps(res)  

def user_function(xfaas_object) -> SerWOObject:
    """
    Calculate sentiment metrics for the given text content.

    Args:
        xfaas_object (SerWOObject): The input SerWOObject containing text content.

    Returns:
        SerWOObject or None: A new SerWOObject containing calculated sentiment metrics, or None if an error occurs.
    """
    try:
        body = xfaas_object.get_body()
        text = body['transcribed_text']
        result = handle(text)
        ret_str = {"sentiment": result}
        s = SerWOObject(body=ret_str)
        return s
    
    except Exception as e:
        print("Error in function:", e)
        return None