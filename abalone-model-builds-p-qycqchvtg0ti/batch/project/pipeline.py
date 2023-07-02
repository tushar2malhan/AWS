import os
import boto3
import json
import uuid

import sagemaker
import sagemaker.session
from sagemaker import get_execution_role
from sagemaker.model import Model
from sagemaker.pipeline import PipelineModel
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import CreateModelStep, TransformStep
from sagemaker.inputs import CreateModelInput, TransformInput
from sagemaker.workflow.parameters import (
    ParameterString,
    ParameterFloat,
    ParameterInteger,)

from sagemaker.transformer import Transformer



BASE_DIR = os.path.dirname(os.path.realpath(__file__))
# get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(os.getcwd(), "batch", "project"))
# load the config file
with open(os.path.join(project_dir, "config.json")) as f:
    config = json.load(f)

 ####  Batch tranformation Variables from config file
input_path_batch_libsvm = config["input_path_batch_libsvm"]
transform_instances_type = config["transform_instances_type"]
processing_ins_count = config["processing_instance_count"]
JobName = config["JobName"]
BatchTransformer_Step_name= config['BatchTransformer_Step_name']
BatchPipeline_name= config['BatchPipeline_name']
BatchCreateModel_step_name= config['BatchCreateModel_step_name']

def get_sagemaker_client(region):
     """Gets the sagemaker client.

        Args:
            region: the aws region to start the session
            default_bucket: the bucket to use for storing the artifacts

        Returns:
            `sagemaker.session.Session instance
        """
     boto_session = boto3.Session(region_name=region)
     sagemaker_client = boto_session.client("sagemaker")
     return sagemaker_client

def get_session(region, default_bucket):
    """Gets the sagemaker session based on the region.

    Args:
        region: the aws region to start the session
        default_bucket: the bucket to use for storing the artifacts

    Returns:
        `sagemaker.session.Session instance
    """

    boto_session = boto3.Session(region_name=region)

    sagemaker_client = boto_session.client("sagemaker")
    runtime_client = boto_session.client("sagemaker-runtime")
    return sagemaker.session.Session(
        boto_session=boto_session,
        sagemaker_client=sagemaker_client,
        sagemaker_runtime_client=runtime_client,
        default_bucket=default_bucket,
    )

def get_pipeline_custom_tags(new_tags, region, sagemaker_project_arn=None):
    try:
        sm_client = get_sagemaker_client(region)
        response = sm_client.list_tags(
            ResourceArn=sagemaker_project_arn)
        project_tags = response["Tags"]
        for project_tag in project_tags:
            new_tags.append(project_tag)
    except Exception as e:
        print(f"Error getting project tags: {e}")
    return new_tags

def get_pipeline(
    region,
    sagemaker_project_arn=None,
    role=None,
    default_bucket=None,
    model_package_group_name=None,
    pipeline_name= f'{BatchPipeline_name}{uuid.uuid4()}',
    base_job_prefix=JobName,
    ):

    sagemaker_session = get_session(region=region, default_bucket=default_bucket)
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    #### Accessing Variables
    input_path_ = f"s3://{default_bucket}/project/{input_path_batch_libsvm}"
    print('S3 path of the input file:', input_path_)
    input_path = ParameterString(name='InputPath', default_value=input_path_)
    output_path = ParameterString(name='OutputPath', default_value= f's3://{default_bucket}/output/')
    content_type = ParameterString(name='ContentType', default_value='text/csv')
    compression_type = ParameterString(name='CompressionType', default_value='None')
    instance_type = ParameterString(name='InstanceType', default_value=transform_instances_type[0])
    instance_count = ParameterInteger(name='InstanceCount', default_value=processing_ins_count)
    max_payload_in_mb = ParameterInteger(name='MaxPayloadInMB', default_value=6)
    batch_data = ParameterString(name="BatchData", default_value=input_path_)
   
    model_approval_status = 'Approved'

    sm = boto3.client('sagemaker')
    response = sm.list_model_packages(
        ModelPackageGroupName=model_package_group_name,
        ModelApprovalStatus=model_approval_status)
    latest_approved_model = response['ModelPackageSummaryList'][0]['ModelPackageArn']  
    # Get the latest approved model package
    model_package_details = sm.describe_model_package(ModelPackageName=latest_approved_model)
    print("Latest Approved model's detail information ", model_package_details )
    model_data_url = model_package_details['InferenceSpecification']['Containers'][0]['ModelDataUrl']


    # Define the model
    model = Model(
        image_uri=model_package_details['InferenceSpecification']['Containers'][0]['Image'],
        model_data=model_data_url,
        sagemaker_session=sagemaker_session,
        role=role,)

    # Define the CreateModelStep
    create_model_step = CreateModelStep(
        name=BatchCreateModel_step_name,
        model=model,
        inputs=CreateModelInput(instance_type=instance_type, accelerator_type="ml.eia1.medium"),
    )

    # Define the Transformer
    transformer = Transformer(
        model_name=create_model_step.properties.ModelName,
        instance_type=instance_type,  
        instance_count=instance_count,
        output_path=output_path,
    )
    # Define the TransformStep
    step_transform = TransformStep(
        name=BatchTransformer_Step_name,
        transformer=transformer,
        inputs=TransformInput(data=batch_data),
    )
    
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            input_path,
            output_path,
            content_type,
            compression_type,
            instance_type,
            instance_count,
            max_payload_in_mb,
            batch_data
        ],
        steps=[create_model_step, step_transform],
        sagemaker_session=sagemaker_session,
    )

    return pipeline
