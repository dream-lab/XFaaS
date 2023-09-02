import requests
import base64
import logging
import io
import cv2
import numpy as np
from PIL import Image
import onnxruntime as ort
import os

from python.src.utils.classes.commons.serwo_objects import SerWOObject
from python.src.utils.classes.commons.serwo_objects import *


#////////////////////////////////////////
#           Fetch Data
#////////////////////////////////////////
def download_file(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content
            encoded_image = base64.b64encode(image_data).decode('utf-8')
            return encoded_image
        else:
            with open ('/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/MgrsE2G.jpg', 'rb') as file:
                img_data = file.read()
            encoded_image = base64.b64encode(img_data).decode('utf-8')
            return encoded_image
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def FetchData(xfaas_object: SerWOObject) -> SerWOObject:
    try:
        # body contains the input json data given in postman
        metadata = xfaas_object.get_metadata()
        body = xfaas_object.get_body()
        url = body["url"]

        encoded = download_file(url)
        body["encoded"] = encoded

        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////

#////////////////////////////////////////
#               Grayscale
#////////////////////////////////////////

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


def Grayscale(xfaas_object):
    try:
        body = xfaas_object.get_body()
        encoded_image = body["encoded"]
        image_data = rgb_to_grayscale(encoded_image)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////


#////////////////////////////////////////
#               Flip
#////////////////////////////////////////
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


def Flip(xfaas_object):
    try:
        body = xfaas_object.get_body()
        image_data = body["encoded"]
        image_data = flip(image_data)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////

#////////////////////////////////////////
#               Rotate
#////////////////////////////////////////
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


def Rotate(xfaas_object):
    try:
        body = xfaas_object.get_body()
        image_data = body["encoded"]
        image_data = rotate(image_data)

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////


#////////////////////////////////////////
#               Resize
#////////////////////////////////////////

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


def Resize(xfaas_object):
    try:
        body = xfaas_object.get_body()
        encoded_image = body["encoded"]
        image_data = encode(resize(decode(encoded_image)))

        body["encoded"] = image_data
        metadata = xfaas_object.get_metadata()
        return SerWOObject(body=body, metadata=metadata)
    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function",e)
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////

#////////////////////////////////////////
#     Resnet / AlexNet / MobileNet
#////////////////////////////////////////
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


def InferResnet(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        img_base64 = body['encoded']
        base = serwoObject.get_basepath()
        base = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/resnet/'
        img = decode_base64(img_base64)
        img = preprocess(img)
        model_path = f'{base}dependencies/models/resnet50v2.onnx'
        outputs = run_model(model_path, img)

        image_class = map_outputs(outputs,base)
        ret_val = {"resnet": image_class}
        return SerWOObject(body=ret_val)

    except Exception as e:
        logging.info(f'exception in resnet: {e}')
        raise Exception("[SerWOLite-Error]::Error at user function",e)


def InferAlexNet(serwoObject) -> SerWOObject:
    try:
        body = serwoObject.get_body()
        img_base64 = body['encoded']
        base = serwoObject.get_basepath()
        base = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/alexnet/'
        img = decode_base64(img_base64)
        img = preprocess(img)
        model_path = f'{base}dependencies/models/bvlcalexnet-12-int8.onnx'
        outputs = run_model(model_path, img)

        image_class = map_outputs(outputs,base)
        ret_val = {"resnet": image_class}
        return SerWOObject(body=ret_val)

    except Exception as e:
        logging.info(f'exception in resnet: {e}')
        raise Exception("[SerWOLite-Error]::Error at user function",e)
    

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
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////


#////////////////////////////////////////
#               Aggregate
#////////////////////////////////////////
def Aggregate(xfaas_object):
    try:
        print("Inside user function : Aggregator")
        results = []

        for idx, item in enumerate(xfaas_object.get_objects()):
            body = item.get_body()
            results.append(body)
        predictions = {"Predictions": results}
        return SerWOObject(body=predictions)

    except Exception as e:
        print(e)
        raise Exception("[SerWOLite-Error]::Error at user function")
#////////////////////////////////////////
#////////////////////////////////////////
#////////////////////////////////////////

"""
mock function to build serwo list object
"""
def build_serwo_list_object(event):
    list_obj = SerWOObjectsList()
    for record in event:
        list_obj.add_object(body=record.get("body"))
    return list_obj

def build_req_from_file(path):
    with open(path, "r") as file:
        # Write data to the file
        req_txt = file.read()
        req_json = json.loads(req_txt)
        req = SerWOObject.from_json(req_json)
    return req

def write_req_to_file(req, path):
    with open(path, "w") as file:
        # Write data to the file
        file.write(req.to_json())

body = {"url":"https://i.imgur.com/MgrsE2G.jpg"}

req = SerWOObject(body=body)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/fetch/inputs/input.json'
write_req_to_file(req, path)
req = build_req_from_file(path)
img = FetchData(req)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/grayscale/inputs/input.json'
write_req_to_file(img, path)
req = build_req_from_file(path)
gry = Grayscale(req)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/flip/inputs/input.json'
write_req_to_file(gry, path)
req = build_req_from_file(path)
flp = Flip(req)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/rotate/inputs/input.json'
write_req_to_file(flp, path)
req = build_req_from_file(path)
rtt = Rotate(req)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/resize/inputs/input.json'
write_req_to_file(rtt, path)
req = build_req_from_file(path)
rsz = Resize(req)


path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/resnet/inputs/input.json'
write_req_to_file(rsz, path)
req = build_req_from_file(path)
i1 = InferResnet(req)

path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/alexnet/inputs/input.json'
write_req_to_file(rsz, path)
req = build_req_from_file(path)
i2 = InferAlexNet(req)


path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/mobilenet/inputs/input.json'
write_req_to_file(rsz, path)
req = build_req_from_file(path)
i3 = InferMobilenet(req)



# fanin_list = [i1, i2, i3]
# # emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
# fanin_object = [dict(body=obj.get_body()) for obj in fanin_list]
# l_obj = build_serwo_list_object(fanin_object)

fanin_list = [i1, i2, i3]
idx = 0
for r in fanin_list:
    idx = idx+1
    path = f'/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/aggregate/inputs/input{idx}.json'
    write_req_to_file(r, path)
path = '/home/azureuser/XFaaS/serwo/examples/ImageProcessAz/functions/aggregate/inputs/'
file_list = os.listdir(path)

fin_list = []
for filename in file_list:
    if os.path.isfile(os.path.join(path, filename)):
        fin_list.append(build_req_from_file(path+filename))

# emulated return object for lambda of the format ([{"body": val1},..,{"body": val2}])
fanin_object = [dict(body=obj.get_body()) for obj in fin_list]
l_obj = build_serwo_list_object(fanin_object)
res = Aggregate(l_obj)

print(res.get_body())