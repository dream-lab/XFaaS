import boto3
from datetime import datetime, timedelta
import sys, pytz, csv

ist_timezone = pytz.timezone('Asia/Kolkata')

def add_lists_by_index(list1, list2):
    max_size = max(len(list1), len(list2))  # Determine the maximum size of the resultant list
    result = []

    for i in range(max_size):
        element1 = list1[i] if i < len(list1) else 0  # Use 0 if index is out of range for list1
        element2 = list2[i] if i < len(list2) else 0  # Use 0 if index is out of range for list2
        result.append(element1 + element2)

    return result


def get_max_concurrent_execs(func_name):
    # Initialize the CloudWatch client
    cloudwatch_client = boto3.client('cloudwatch', region_name='ap-south-1')

    # Specify the metric data query
    metric_data_query = {
        'Id': 'concurrentExecutions',
        'MetricStat': {
            'Metric': {
                'Namespace': 'AWS/Lambda',
                'MetricName': 'ConcurrentExecutions',
                'Dimensions': [
                    {
                        'Name': 'FunctionName',
                        'Value': func_name
                    }
                ]
            },
            'Period': 60,
            'Stat': 'Maximum'
        },
        'ReturnData': True
    }

    # Calculate the start and end times
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1000)

    # Convert start and end times to ISO 8601 format
    start_time_iso = start_time.strftime('%Y-%m-%dT%H:%M:%S')
    end_time_iso = end_time.strftime('%Y-%m-%dT%H:%M:%S')

    # Perform the get-metric-data operation
    response = cloudwatch_client.get_metric_data(
        MetricDataQueries=[metric_data_query],
        StartTime=start_time_iso,
        EndTime=end_time_iso,
    )

    timestamps = response['MetricDataResults'][0]['Timestamps']
    concurrent_execs = response['MetricDataResults'][0]['Values']

    return timestamps, concurrent_execs


def get_container_count():
    # Initialize the Lambda client
    lambda_client = boto3.client('lambda', region_name='ap-south-1')

    # Replace 'YourLayerName-' with the actual name of your Lambda application (Layer)
    wf_name = sys.argv[1]
    application_name_prefix = wf_name

    # Initialize an empty list to store all functions
    all_functions = []

    # Initial call to list_functions
    response = lambda_client.list_functions()

    # Filter and add the functions with the correct prefix
    all_functions.extend([func for func in response['Functions'] if func['FunctionName'].startswith(application_name_prefix)])

    # Check if there are more functions to retrieve
    while 'NextMarker' in response:
        next_marker = response['NextMarker']
        response = lambda_client.list_functions(Marker=next_marker)
        all_functions.extend([func for func in response['Functions'] if func['FunctionName'].startswith(application_name_prefix)])

    # Sort the functions by their names
    all_functions.sort(key=lambda x: x['FunctionName'])
    concurrent_executions = {}

    # Initialize variables to track the minimum and maximum timestamps
    min_timestamp = None  # Initialize to positive infinity
    max_timestamp = None  # Initialize to negative infinity

    for function in all_functions:
        t, c = get_max_concurrent_execs(function['FunctionName'])
        for i in range(len(t)):
            timestamp = t[i]
            concurrent = c[i]

            if min_timestamp is None or timestamp < min_timestamp:
                min_timestamp = timestamp
            if max_timestamp is None or timestamp > max_timestamp:
                max_timestamp = timestamp

            timestamp = timestamp.astimezone(ist_timezone)
            timestamp = timestamp.strftime('%s')

            if timestamp in concurrent_executions:
                concurrent_executions[timestamp] += concurrent
            else:
                concurrent_executions[timestamp] = concurrent

    # timestamps.sort()
    print(concurrent_executions)
    min_timestamp = min_timestamp.astimezone(ist_timezone)

    op_file = f"aws_ap_south_1_{wf_name}_{min_timestamp.strftime('%d-%m-%Y-%H-%M-%S')}.txt"

    with open(op_file, 'w', newline='') as ofile:
        csvwriter = csv.writer(ofile)

        for ti, val in concurrent_executions.items():
            csvwriter.writerow([ti, val])

    return concurrent_executions

get_container_count()