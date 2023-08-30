import requests
import base64
import logging
import sys
from PIL import Image
import io
import numpy as np
import cv2
import onnxruntime as ort
import objsize


def download_file(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            return encoded_image
        else:
            logging.info(f"Failed to download image. Status code: {response.status_code}")
            return None
    except Exception as e:
        logging.info(f"An error occurred: {e}")
        return None

def rgb_to_grayscale(encoded_image):
    """image_data is the data read from image using read()"""
    image_data = base64.b64decode(encoded_image.encode('utf-8'))
    img = Image.open(io.BytesIO(image_data))
    img_grayscale = img.convert("L")
    img_byte_arr = io.BytesIO()
    img_grayscale.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    encoded_image = base64.b64encode(img_byte_arr).decode('utf-8')
    return encoded_image

def flip(encoded_image):
    try:
        image_data = base64.b64decode(encoded_image.encode('utf-8'))

        # Create a BytesIO object to simulate a file-like object
        image_io = io.BytesIO(image_data)

        # Open the image as a PIL Image object
        image = Image.open(image_io)

        # Flip the image vertically (top to bottom)
        flipped_image = image.transpose(Image.FLIP_TOP_BOTTOM)

        # Create a new BytesIO object to store the flipped image
        flipped_image_io = io.BytesIO()

        # Save the flipped image as PNG format to the new BytesIO object
        flipped_image.save(flipped_image_io, format='PNG')

        # Get the bytes of the flipped image
        flipped_image_bytes = flipped_image_io.getvalue()

        # Encode the flipped image as base64
        encoded_flipped_image = base64.b64encode(flipped_image_bytes).decode('utf-8')

        return encoded_flipped_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def rotate(encoded_image):
    try:
        image_data = base64.b64decode(encoded_image.encode('utf-8'))
        # Create a BytesIO object to simulate a file-like object
        image_io = io.BytesIO(image_data)

        # Open the image as a PIL Image object
        image = Image.open(image_io)

        # Rotate the image
        rotated_image = image.rotate(-90, expand=True)

        # Create a new BytesIO object to store the flipped image
        rotated_image_io = io.BytesIO()

        # Save the flipped image as PNG format to the new BytesIO object
        rotated_image.save(rotated_image_io, format='PNG')

        # Get the bytes of the flipped image
        rotated_image_bytes = rotated_image_io.getvalue()

        # Encode the flipped image as base64
        encoded_rotated_image = base64.b64encode(rotated_image_bytes).decode('utf-8')

        return encoded_rotated_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def decode(image_json):
    decoded_image = base64.b64decode(image_json.encode('utf-8'))
    jpeg_as_np = np.frombuffer(decoded_image, dtype=np.uint8)
    image = cv2.imdecode(jpeg_as_np, flags=1)
    return image


def resize(img_from_request):
    resized_img = cv2.resize(img_from_request, (224, 224))
    return resized_img


def encode(image):
    retval, buffer = cv2.imencode('.jpg', image)
    encoded_im = base64.b64encode(buffer)
    image = encoded_im.decode('utf-8')
    return image

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
def map_outputs(outputs, path):
    labels = load_labels(path)
    return labels[np.argmax(outputs)]


def run_model(model_path, img):
    ort_sess = ort.InferenceSession(model_path)
    input_name = ort_sess.get_inputs()[0].name
    outputs = ort_sess.run(None, {input_name: img})

    return outputs

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

def agg(l):
    results = []

    for idx, item in enumerate(l):
        body = l[idx]
        results.append(body)
    predictions = {"Predictions": results}

    return predictions



#----------------------------------------------------------------
#----------------------------------------------------------------


body = {"url": str(sys.argv[1])}

enc_img = download_file(body['url'])
sz = objsize.get_deep_size(enc_img)
print(f'Output size donwload_file : {sz}')
print("---------------------------------------------")


sz = objsize.get_deep_size(enc_img)
print(f'Input size grayscale : {sz}')
gr_enc_img = rgb_to_grayscale(enc_img)
sz = objsize.get_deep_size(gr_enc_img)
print(f'Output size grayscale : {sz}')
print("---------------------------------------------")



sz = objsize.get_deep_size(gr_enc_img)
print(f'Input size flip : {sz}')
fl_img = flip(gr_enc_img)
sz = objsize.get_deep_size(fl_img)
print(f'Output size flip : {sz}')
print("---------------------------------------------")


sz = objsize.get_deep_size(fl_img)
print(f'Input size rotate : {sz}')
rt_img = rotate(fl_img)
sz = objsize.get_deep_size(rt_img)
print(f'Output size rotate : {sz}')
print("---------------------------------------------")


sz = objsize.get_deep_size(rt_img)
print(f'Input size resize : {sz}')
res_img = encode(resize(decode(rt_img)))
sz = objsize.get_deep_size(res_img)
print(f'Output size resize : {sz}')
print("---------------------------------------------")


# Resnet
sz = objsize.get_deep_size(res_img)
print(f'Input size Resnet : {sz}')
img = decode_base64(res_img)
img = preprocess(img)
model_path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/models/mobilenetv2-12.onnx'
path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/resnet/dependencies/data/imagenet_classes.txt'
outputs = run_model(model_path, img)
image_class = map_outputs(outputs, path)
ret_val = {"resnet": image_class}
sz = objsize.get_deep_size(ret_val)
print(f'Output size Resnet : {sz}')
print("---------------------------------------------")



# Mobilenet
sz = objsize.get_deep_size(img)
print(f'Input size Mobilenet : {sz}')
img = preprocess(img)
model_path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/models/mobilenetv2-12.onnx'
path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/mobilenet/dependencies/data/imagenet_classes.txt'
outputs = run_model(model_path, img)
image_class = map_outputs(outputs,path)
ret_val1 = {"mobilenet": image_class}
sz = objsize.get_deep_size(ret_val1)
print(f'Output size Mobilenet : {sz}')
print("---------------------------------------------")



# Alexnet
sz = objsize.get_deep_size(img)
print(f'Input size Alexnet : {sz}')
img = preprocess(img)
model_path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/models/bvlcalexnet-12-int8.onnx'
path = '/home/nikhil/work/XFaaS/serwo/examples/ImageProcessAz/alexnet/dependencies/data/imagenet_classes.txt'
outputs = run_model(model_path, img)
image_class = map_outputs(outputs,path)
ret_val2 = {"alexnet": image_class}
sz = objsize.get_deep_size(ret_val2)
print(f'Output size Alexnet : {sz}')
print("---------------------------------------------")



l = [ret_val, ret_val1, ret_val2]

sz = objsize.get_deep_size(l)
print(f'Input size Agg : {sz}')
res = agg(l)
sz = objsize.get_deep_size(res)
print(f'Output size Agg : {sz}')
print("---------------------------------------------")