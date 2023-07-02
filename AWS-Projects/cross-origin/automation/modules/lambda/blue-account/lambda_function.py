import zlib
import base64
import json
import boto3
import uuid
import os

s3 = boto3.client('s3')

def read_config_from_s3(bucket_name, object_key):
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = response['Body'].read().decode('utf-8')
    return content


# Create a CloudWatchLogs client
logs = boto3.client('logs')

def lambda_handler(event, context):
    
    
    # Extract log stream name and log events from the CloudTrail event
    log_stream_name = event['detail']['requestParameters']['logStreamName']
    log_group_name = event['detail']['requestParameters']['logGroupName']
    print('Event > ',event)
    print('log group name for above event is ', log_group_name, 'and log stream name is ',log_stream_name )

    # Use the FilterLogEvents method to get all the log events from the log group and log stream
    response = logs.filter_log_events(
        logGroupName=log_group_name,
        logStreamNames=[log_stream_name],
        interleaved=True
    )
    
    config_file_key_ = os.environ['config_file_key_name']
    config_file_content = read_config_from_s3("paysafe-upf-dataops-properties", config_file_key_)
    config = json.loads(config_file_content)
    print('config', config)
    if config.get('flag_execute_lambda_blue') == 'yes':
        
        # Loop through each log event and send it to the Kinesis data stream "kinesis stream"
        for log_event in response['events']:
            message = log_event['message']
            print("Message Log: ", message)
            try:
                # Put the message in the Kinesis data stream
                kinesis = boto3.client('kinesis')
                response = kinesis.put_record(
                    StreamName=os.environ['kinesis_stream_name'],
                    Data=json.dumps(message),
                    PartitionKey=str(uuid.uuid4())
                )
                print(f'Successfully sent message to Kinesis data stream. Response: {response}')
            except Exception as e:
                print(f'Error sending message to Kinesis data stream. Error: {e}')
                return e
        return response
    
    else:
        print('Lambda execution Blocked')
        return f"Check config file in paysafe-upf-dataops-properties s3 bucket to run the operations! "
