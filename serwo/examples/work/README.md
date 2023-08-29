# VIDEO PROCESSING

This workflow contains functions that downloads the video from S3 and fans them out into two functions `Gray scaling` and `Face detection`. The output from these functions are sent to a function that converts the video to `.gif` format and then compresses the gif files and upload the compressed folder to S3.

## Hyperlink to the list of functions

-[functions.txt](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/custom_workflows/work/functions.txt)

## Hyperlink to the individual functions

-[DownloadFromS3](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/DownloadFromS3/download.py) -[FaceDetection](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/FaceDetection/detection.py) -[GrayScaling](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/GrayScaling/grayscale.py) -[VideoToGif](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/VideoToGif/videogif.py) -[CompressToZip](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/CompressToZip/compression.py) -[UploadToS3](https://github.com/dream-lab/xfaas-workloads/tree/ragul-swathika/workflows/work/UplaodToS3/upload.py)

## Description of input parameters

**Input Parameters**

- `input` : Input Bucket Name
- `output`: Output Bucket Name
- `Object Key` : Name of the video file
- `Model Key` : Name of the face detection model

## Description of output parameters

**Output Parameters**

- `bucket` : Output bucket name
- `Result` : contains the result (If done successfully or not)

## Sample input json

```json
{
  "input": "xfaas-workloads-sprint",
  "output": "xfaas-workloads-sprint",
  "modelKey": "model.xml",
  "objectKey": "ragul-swathika-sample.mp4"
}
```

## Sample output json

```json
{
    "message": "Success",
    "result": {
        "body": {
            "result_of_upload": {
                "bucket": "xfaas-workloads-sprint",
                "result": "Zip folder uploaded successfully"
            }
        },
        "metadata": null,
        "statusCode": 200
    },
    "statusCode": 200
}
```

## Dependencies

To execute this workflow, you will need the following:

1. **Python 3 or higher:** The programming language used for writing the scripts.

2. **Python Packages:**

   - `base64:` A module for encoding and decoding binary data to and from ASCII strings.
   - `boto3:` The AWS SDK for Python.
   - `uuid:` A module to generate universally unique identifiers (UUIDs).
   - `time:` A Python module for measuring execution time.
   - `cv2:` OpenCV, a library for computer vision tasks.
   - `tempfile:` A module for creating temporary files and directories.
   - `Psutil:` A cross-platform library for accessing system details and managing processes.

Make sure to install these packages using pip before running your code. You can install them using the following command:

```bash
pip install boto3 uuid opencv-python psutil
```

## Visual representation of the workflow

[![](https://mermaid.ink/img/pako:eNqFkMFqwzAMhl8l6ORC-wI5DNq4ya2XZjsUX4SttGaxZRyHUtq--7yCIYNBdZL0ff9BuoNmQ1DDMPJVXzCmqpfKV7m2QvLVj4zmyxriQ_ZW1Wbz8age1U50EW9HjaP15xd5n2lEi5okJdLJsl-kdkWR4hXrubPDgjeF7__nsvBWNOxCpGnq-WTDQtm_V9qidOIz_D0B1uAoOrQmf-r-qytIF3KkoM6twfitQPln9nBOfLx5DXWKM61hDgYTSYvniA7qAccpbwP6E3OZnz9C2nza?type=png)](https://mermaid.live/edit#pako:eNqFkMFqwzAMhl8l6ORC-wI5DNq4ya2XZjsUX4SttGaxZRyHUtq--7yCIYNBdZL0ff9BuoNmQ1DDMPJVXzCmqpfKV7m2QvLVj4zmyxriQ_ZW1Wbz8age1U50EW9HjaP15xd5n2lEi5okJdLJsl-kdkWR4hXrubPDgjeF7__nsvBWNOxCpGnq-WTDQtm_V9qidOIz_D0B1uAoOrQmf-r-qytIF3KkoM6twfitQPln9nBOfLx5DXWKM61hDgYTSYvniA7qAccpbwP6E3OZnz9C2nza)

## Authors

- [Ragul B](https://www.github.com/raguwull)
- [Swathika D](https://www.github.com/DSwathika)