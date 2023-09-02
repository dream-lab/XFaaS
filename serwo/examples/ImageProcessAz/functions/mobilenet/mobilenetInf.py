import numpy as np
import base64
import io
from PIL import Image
import onnxruntime as ort
import logging
from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import build_req_from_file



def decode_base64(data):
    img = np.asarray(Image.open(io.BytesIO(base64.b64decode(data))))[:, :, [2, 1, 0]]
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

def InferMobilenet(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        img_base64 = body['encoded']
        base = serwoObject.get_basepath()
        base = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/mobilenet/'
        img = decode_base64(img_base64)
        img = preprocess(img)
        model_path = f'{base}dependencies/models/mobilenetv2-12.onnx'
        outputs = run_model(model_path, img)

        image_class = map_outputs(outputs,base)
        ret_val = {"resnet": image_class}
        return SerWOObject(body=ret_val)

    except Exception as e:
        logging.info(f'exception in resnet: {e}')
        raise Exception("[SerWOLite-Error]::Error at user function",e)


path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/resnet/inputs/input.json'
req = build_req_from_file(path)
i1 = InferMobilenet(req)