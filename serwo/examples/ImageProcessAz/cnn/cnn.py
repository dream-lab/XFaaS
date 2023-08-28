# {\"body\":\"test_string\",\"metadata\":\"test_metadata\"}

# Python base imports
from time import time
import torch
from PIL import Image
from torchvision import transforms
import base64


import os

import io
import joblib


# XFaaS specific imports
from python.src.utils.classes.commons.serwo_objects import SerWOObject


def decodeAndSaveModel(modeldata, modelkey, dependenciesPath):
    with open(dependenciesPath + modelkey, "wb") as f:
        f.write(modeldata)
        return dependenciesPath + modelkey


def handle(imagedata, modeldata, dependenciesPath, modelkey):
    # Decoding the image
    start = time()
    decoded_data = base64.b64decode(imagedata.encode('utf-8'))

    input_image = Image.open(io.BytesIO(decoded_data)).convert("RGB")

    # Preprocessing the input image
    preprocess = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    input_tensor = preprocess(input_image)
    input_batch = input_tensor.unsqueeze(0)

    # Decoding the model
    model_path = decodeAndSaveModel(modeldata, modelkey, dependenciesPath)

    # Loading the model from local storage
    model = joblib.load(open(model_path, "rb"))

    # Put the model in the eval mode
    model.eval()

    # Carry out the inference
    out = model(input_batch)
    print("output shape:", out.shape)

    # Decoding the dataset
    dataset_name = "imagenet_classes.txt"
    dataset_path = f"{dependenciesPath}/{dataset_name}"

    with open(dataset_path, "r") as f:
        classes = [line.strip() for line in f.readlines()]

    _, index = torch.max(out, 1)
    percentage = torch.nn.functional.softmax(out, dim=1)[0] * 100
    print(classes[index[0]], percentage[index[0]].item())

    _, indices = torch.sort(out, descending=True)
    top_predictions = [(classes[idx], percentage[idx].item()) for idx in indices[0][:5]]
    end = time() - start

    return top_predictions, end


def user_function(xfaas_object):
    try:
        body = xfaas_object.get_body()

        image_data = body["encoded"]

        modelkey = body["cnnmodelkey"]
        cnnmodeldata = body["cnnmodeldata"]
        dependenciesPath = xfaas_object.get_basepath() + "dependencies/"
        if not os.path.exists(dependenciesPath):
            os.makedirs(dependenciesPath)
        predictions, latency = handle(
            image_data, cnnmodeldata, dependenciesPath, modelkey
        )
        # choose the top 1 predictions
        result = {}
        result["prediction"] = predictions[0][0]

        result["model"] = "cnn"

        return SerWOObject(body=result)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
