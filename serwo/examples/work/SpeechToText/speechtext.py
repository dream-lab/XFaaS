import base64
import io
import speech_recognition as sr
from python.src.utils.classes.commons.serwo_objects import SerWOObject

def handle(base64_wav_audio):
    """
    Transcribes the content of a base64-encoded WAV audio.

    Args:
        base64_wav_audio (str): The base64-encoded string of the WAV audio.

    Returns:
        str: The transcribed text from the audio.
    """
    finalData = ''
    try:
        r = sr.Recognizer()
        audio_binary = base64.b64decode(base64_wav_audio)
        audio_bytesio = io.BytesIO(audio_binary)
        with sr.AudioFile(audio_bytesio) as source:
            audio_data = r.listen(source)
            finalData = r.recognize_google(audio_data)

    except Exception as e:
        print("Following error was observed:", e)
        print("Exiting the code.")
        exit(0)
    
    return finalData

def user_function(xfaas_object) -> SerWOObject:
    """
    User function to transcribe a base64-encoded WAV audio.

    Args:
        xfaas_object (SerWOObject): The input SerWOObject containing base64_audio_string.

    Returns:
        SerWOObject: A new SerWOObject containing the transcribed_text.
    """
    try:
        body = xfaas_object.get_body()
        encoded_wav_base64 = body['audio']
        transcribed_text = handle(encoded_wav_base64)
        ret_str = {"transcribed_text": transcribed_text}
        s = SerWOObject(body=ret_str)
        return s
    
    except Exception as e:
        print("Error in function:", e)
        return None