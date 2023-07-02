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
    logs = boto3.client('logs')
    log_stream_name = event['detail']['requestParameters']['logStreamName']
    log_group_name = event['detail']['requestParameters']['logGroupName']
    print('Event > ',event)
    print('log group name for above event is ', log_group_name, 'and log stream name is ',log_stream_name )
    
    response = logs.filter_log_events(
        logGroupName=log_group_name,
        logStreamNames=[log_stream_name],
        interleaved=True
    )

    sts = boto3.client('sts')
    assumed_role = sts.assume_role(
        RoleArn=f'arn:aws:iam::{os.environ["blue_account_id"]}:role/{os.environ["role_name"]}',
        RoleSessionName='kinesis_writer'
    )
    
    kinesis = boto3.client(
        'kinesis',
        region_name='ca-central-1',
        aws_access_key_id=assumed_role['Credentials']['AccessKeyId'],
        aws_secret_access_key=assumed_role['Credentials']['SecretAccessKey'],
        aws_session_token=assumed_role['Credentials']['SessionToken']
    )

    config_file_key_ = os.environ['config_file_key_name']
    config_file_content = read_config_from_s3("paysafe-upf-dataops-properties", config_file_key_)
    config = json.loads(config_file_content)
    print('config', config)
    if config.get('flag_execute_lambda_yellow') == 'yes':

        for log_event in response['events']:
            message = log_event['message']
            print("Message Log: ", message)
            try:
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
        print( "Check config file key value in 'paysafe-upf-dataops-properties' s3 bucket to run the operations! ")
        return('Lambda execution Blocked')