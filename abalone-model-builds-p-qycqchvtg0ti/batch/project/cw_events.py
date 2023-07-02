import boto3


events = boto3.client('events')

# Define rule schedule at 9 pm
rule_schedule = 'cron(0 21 * * ? *)'

# Define rule target (SageMaker pipeline execution)
rule_target = {
    'Arn': 'arn:aws:sagemaker:us-east-1:123456789012:execution-pipeline/sagemaker-project-pipeline/1234567890123456',
    'Id': 'sagemaker-project-pipeline'
}

# Create CloudWatch Events rule
events.put_rule(
    Name='sagemaker-project-batch-transformation',
    ScheduleExpression=rule_schedule,
    State='ENABLED',
    Description='Schedule for SageMaker project batch transformation'
)

# Add SageMaker pipeline execution as target for rule
events.put_targets(
    Rule='sagemaker-project-batch-transformation',
    Targets=[
        rule_target
    ]
)
