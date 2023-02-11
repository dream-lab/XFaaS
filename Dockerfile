FROM ubuntu:20.04
RUN apt update 
RUN apt install -y python3 python3-pip git curl unzip wget
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
RUN curl  -LO https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip 
RUN unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
RUN ./sam-installation/install
RUN curl -sL https://aka.ms/InstallAzureCLIDeb | bash
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt install -y openjdk-11-jdk
RUN curl -LO https://dlcdn.apache.org//jmeter/binaries/apache-jmeter-5.5.tgz
RUN tar xf apache-jmeter-5.5.tgz
ENV PATH "$PATH:/apache-jmeter-5.5/bin"
ENTRYPOINT ["tail", "-f", "/dev/null"]
