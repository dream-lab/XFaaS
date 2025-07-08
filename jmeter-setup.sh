#!/bin/bash

wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.2.zip
sudo apt update
sudo apt install openjdk-11-jre-headless -y
sudo apt install openjdk-11-jdk-headless -y
sudo apt install unzip
unzip apache-jmeter-5.6.2.zip
