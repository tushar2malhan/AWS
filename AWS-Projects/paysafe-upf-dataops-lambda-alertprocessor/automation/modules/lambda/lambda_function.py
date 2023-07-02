import json
import boto3
import uuid as uuid


def lambda_handler(event, context):
    """
        lambda function to submit 
        logs to dynamodb table
    """
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('alertDashboard_logs')
    client = boto3.client('logs')

    try:
        log_stream_name = event.get('detail')\
            .get('requestParameters').get('logStreamName')
        log_group_name = event.get('detail')\
            .get('requestParameters').get('logGroupName')
        logs = client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name)
        logs['events'].append({
            'logGroupName ': log_group_name,
            'logStreamName': log_stream_name})
        print("Events: ", logs['events'])
        
        table.put_item(
            Item={
                'event': str(uuid.uuid4()),
                'log_events': str(logs['events']),
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name
            }
        )
        print(" ***** Lambda Initiated ***** |\
        Logs added to DynamoDB table successfully  |")

    except Exception as e:
        print(f" Events: No Log events found = {e}")
        return json.loads(json.dumps(f"No Log events found =>{e}"))
    return event
