import base64
import boto3
import json
import os
import uuid
from datetime import datetime

def lambda_handler(event, context):
    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record["kinesis"]["data"])
        res = json.loads(payload)

        # generate a unique ID
        unique_id = str(uuid.uuid4())

        # Convert data to dictionary
        data = json.loads(res)

        # add the unique ID to the data as the primary key
        data["id"] = unique_id

        # get the current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        print(data)
        # check if the data type is ExecutionStarted
        if data.get('type') == 'ExecutionStarted':
            # add start time and execution arn to data
            data['start_time'] = current_time
            data['execution_arn'] = data.get('execution_arn')

        if data.get('type') in ['ExecutionSucceeded', 'ExecutionFailed']:
            # add end time and execution arn to data
            data['end_time'] = current_time
            data['execution_arn'] = data.get('execution_arn')

            # add status based on type
            if data.get('type') == 'ExecutionSucceeded':
                data['status'] = 'Success'
            elif data.get('type') == 'ExecutionFailed':
                data['status'] = 'Failed'

        if os.environ['yellow_account_id'] in data.get('execution_arn', '').split(":"):
            data['Zone'] = 'Yellow'
        elif os.environ['grey_account_id'] in data.get('execution_arn', '').split(":"):
            data['Zone'] = 'Grey'
        else:
            data['Zone'] = 'Blue'

        # remove the executionArn key from data as it's no longer needed
        # data.pop('execution_arn', None)

        dynamodb = boto3.resource('dynamodb', region_name="ca-central-1")
        table = dynamodb.Table(os.environ['dynamodb_name'])
        table.put_item(Item=data)

        print("Object successfully stored in DB.", data)
