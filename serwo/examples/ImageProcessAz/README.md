
# XFaaS Workflow for Image Classification 


### Introduction

This README file provides a brief overview and step-by-step guide for image classificarion using the XFaaS workflow. This workflow aims to convert image to grayscale, flip,rotate, and classify the image using Alexnet, Resnet, CNN.

[![](https://mermaid.ink/img/pako:eNp9kc1uwyAQhF8F7Tl5AR8quXGT5tAc0t4ghxVe26j8RIDVRlHevRTH_ZFIxGWZmQ9G2jNI1xJU0Gn3IQf0kb01wjLGat5RlMPWYE8Htlw-sEe-8XgKEjUdcuSvkBMrvtbqOJnXOesN37uI8Yr93LL3NP3zkmroyf-n5Mya5xpSYwiqUxKjcrbW9GkpTkwB2pSgPYVfpgA9l6DVbjcTd5vkF7a87ntPPUbnZ-pelVvMzSYFYD6MwQIMeYOqTTs9fysC4kCGBFRpbNG_CxD2knI4Rvd6shKq6EdawHhs01Iahb1HA1WHOtDlC_Z7uH8?type=png)](https://mermaid.live/edit#pako:eNp9kc1uwyAQhF8F7Tl5AR8quXGT5tAc0t4ghxVe26j8RIDVRlHevRTH_ZFIxGWZmQ9G2jNI1xJU0Gn3IQf0kb01wjLGat5RlMPWYE8Htlw-sEe-8XgKEjUdcuSvkBMrvtbqOJnXOesN37uI8Yr93LL3NP3zkmroyf-n5Mya5xpSYwiqUxKjcrbW9GkpTkwB2pSgPYVfpgA9l6DVbjcTd5vkF7a87ntPPUbnZ-pelVvMzSYFYD6MwQIMeYOqTTs9fysC4kCGBFRpbNG_CxD2knI4Rvd6shKq6EdawHhs01Iahb1HA1WHOtDlC_Z7uH8)


### Function Descriptions

#### fetchImage -
This function fetches the image from the S3 bucket and returns the image data in base64 encoded format.
#### rgb2Gray -
In this step,The fetched image is converted to grayscale.

#### flip -
In this step,The fetched image is flipped.
#### rotate -
In this step,The fetched image is rotated.

### fetchModels-
In this step, the models are fetched from the S3 bucket and stored in the /dependencies directory and encoded in base64 format.

#### alexnet-
In this step, the image is classified using alexnet model.

#### resnet-
In this step, the image is classified using resnet model.

#### cnn-
In this step, the image is classified using cnn model.

### aggregator-
In this step, the results from the previous 3 steps are aggregated and the final result is returned.



### Request body

```json
{
    "input_bucket" : "xfaas-workloads-sprint",
    "input_key" : "sanjai-testimage.jpg",
    "modelbucket":"xfaas-workloads-sprint",
    "resnetmodelkey":"resnet1",
    "alexnetmodelkey":"alexnet_pretrained.pth",
    "cnnmodelkey":"Squeezenet.sav"

}


```


### Response 
```json
{
    "message": "Success",
    "result": {
        "body": {
            "Predictions": [
                {
                    "model": "cnn",
                    "prediction": "196, miniature_schnauzer"
                },
                {
                    "model": "resnet",
                    "prediction": "toy_poodle"
                },
                {
                    "model": "alexnet",
                    "prediction": "283, Persian_cat"
                }
            ]
        },
        "metadata": null,
        "statusCode": 200
    },
    "statusCode": 200
}
```


## Authors

- [@sanjaibalajee](https://www.github.com/sanjaibalajee)
- [@Yashasvee2003](https://www.github.com/Yashasvee2003)



