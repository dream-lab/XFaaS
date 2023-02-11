#!/bin/sh

# get the model file from s3 bucket
wget https://xfaas-ccgrid23-artifact.s3.ap-south-1.amazonaws.com/resnet50v2.onnx

# add to all folders
folders="smart-grid-fusion-aws smart-grid-fusion-azure smart-grid-multicloud smart-grid-singlecloud-aws smart-grid-singlecloud-azure"
model_filename="resnet50v2.onnx"
for folder in ${folders}
do
    echo "[SETUP]::Adding ${model_filename} to ${folder}"
    cp ${model_filename} serwo/examples/${folder}/src/resnet_25KB/dependencies/model/
done
rm -r ${model_filename}

# install the dependencies
echo "[SETUP] Installing dependencies"
pip3 install -r requirements.txt