import os
from time import time
import base64
import onnxruntime
import numpy as np
import cv2


# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def decodeAndSaveModel(modeldata, modelkey, dependenciesPath):
    with open(dependenciesPath + modelkey, "wb") as f:
        f.write(modeldata)
        return dependenciesPath + modelkey


def decodeAndSaveImage(imagedata, imagekey, dependenciesPath):
    with open(dependenciesPath + imagekey, "wb") as f:
        decoded_data = base64.b64decode(imagedata.encode('utf-8'))
        f.write(decoded_data)
        return dependenciesPath + imagekey


def handle(imagedata, modeldata, modelkey, dependenciesPath):
    model_path = decodeAndSaveModel(modeldata, modelkey, dependenciesPath)
    ort_session = onnxruntime.InferenceSession(model_path)

    image_path = decodeAndSaveImage(imagedata, "image.jpg", dependenciesPath)
    start = time()
    input_image = cv2.imread(image_path)
    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)  # Convert to RGB
    input_image = cv2.resize(input_image, (224, 224))
    input_image = input_image.astype(np.float32)
    input_image /= 255.0
    input_image = np.transpose(input_image, (2, 0, 1))  # Channels first

    input_tensor = np.expand_dims(input_image, axis=0)
    ort_inputs = {ort_session.get_inputs()[0].name: input_tensor}
    ort_outs = ort_session.run(None, ort_inputs)

    out = ort_outs[0]
    print("output shape:", out.shape)
    print(os.getcwd())

    with open(dependenciesPath + "imagenet_classes.txt") as f:
        classes = [line.strip() for line in f.readlines()]

    index = np.argmax(out)
    percentage = np.max(out) * 100
    print(classes[index], percentage)

    indices = np.argsort(out, axis=1)[:, -5:][:, ::-1]
    top_predictions = [(classes[idx], out[0][idx] * 100) for idx in indices[0]]

    end = time() - start

    return top_predictions, end


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()

        image_data = body["encoded"]
        modelkey = body["alexnetmodelkey"]
        alexnetmodeldata = body["alexnetmodeldata"]
        dependenciesPath = xfaas_object.get_basepath() + "dependencies/"
        if not os.path.exists(dependenciesPath):
            os.makedirs(dependenciesPath)
        predictions, latency = handle(image_data, alexnetmodeldata, modelkey, dependenciesPath)
        # choose the top 1 predictions
        result = {}
        result["prediction"] = predictions[0][0]

        result["model"] = "alexnet"

        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
