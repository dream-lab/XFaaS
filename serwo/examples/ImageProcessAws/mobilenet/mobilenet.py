import base64
import numpy as np
# import cv2
import json
import time
import onnxruntime as ort
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from PIL import Image
from io import BytesIO
import logging

# decode base64 image

def decode_base64(data):
    img = np.asarray(Image.open(BytesIO(base64.b64decode(data))))[:, :, [2, 1, 0]]
    img = img.transpose((2, 0, 1))
    img = img.reshape(1, 3, 224, 224)
    return img


# preprocess image
def preprocess(img_data):
    mean_vec = np.array([0.485, 0.456, 0.406])
    stddev_vec = np.array([0.229, 0.224, 0.225])
    norm_img_data = np.zeros(img_data.shape).astype('float32')
    for i in range(img_data.shape[0]):
        # for each pixel and channel
        # divide the value by 255 to get value between [0, 1]
        norm_img_data[i, :, :] = (img_data[i, :, :] / 255 - mean_vec[i]) / stddev_vec[i]
    return norm_img_data


# load text file as list

def load_labels(path):
    labels = []
    with open(path, 'r') as f:
        for line in f:
            labels.append(line.strip())
    return labels


# map mobilenet outputs to classes
def map_outputs(outputs,base):
    labels = load_labels(f'{base}dependencies/data/imagenet_classes.txt')
    return labels[np.argmax(outputs)]


def run_model(model_path, img):
    ort_sess = ort.InferenceSession(model_path)
    input_name = ort_sess.get_inputs()[0].name
    outputs = ort_sess.run(None, {input_name: img})

    return outputs


def user_function(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        img_base64 = body['encoded']
        base = serwoObject.get_basepath()
        img = decode_base64(img_base64)
        img = preprocess(img)
        model_path = f'{base}dependencies/model/mobilenetv2-12.onnx'
        outputs = run_model(model_path, img)

        image_class = map_outputs(outputs,base)
        ret_val = {"mobilenet": image_class}
        return SerWOObject(body=ret_val)

    except Exception as e:
        logging.info(f'exception in resnet: {e}')
        raise Exception("[SerWOLite-Error]::Error at user function",e)