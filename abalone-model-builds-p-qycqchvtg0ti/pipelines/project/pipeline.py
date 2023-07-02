"""

        Description:  Ml Deployment on AWS for classification Model
        Date:         1/06/2023
        Status:       Done
        Author:       Tushar Malhan

        Example workflow pipeline script for the pipeline.
                                          
        Process-> Train -> Evaluate -> Condition -> RegisterModel -> Batch Inference

"""
import os
import json
import boto3
import sagemaker
import sagemaker.session
import pandas as pd
import numpy as np

from sagemaker.estimator import Estimator
import lightgbm
from sagemaker.inputs import TrainingInput
from sagemaker.model_metrics import (
    MetricsSource,
    ModelMetrics,
)
from sagemaker.processing import (
    ProcessingInput,
    ProcessingOutput,
    ScriptProcessor,
)
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.conditions import ConditionLessThanOrEqualTo
from sagemaker.workflow.condition_step import (
    ConditionStep,
    JsonGet,
)
from sagemaker.workflow.parameters import (
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import (
    ProcessingStep,
    TrainingStep,
)
from sagemaker.model import Model
from sagemaker.inputs import CreateModelInput, TransformInput
from sagemaker.workflow.model_step import CreateModelStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.steps import TransformStep
from sagemaker.transformer import Transformer
from sagemaker import image_uris, model_uris, script_uris

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

# get the absolute path of the project directory
project_dir = os.path.abspath(os.path.join(os.getcwd(), "pipelines", "project"))

# load the config file
with open(os.path.join(project_dir, "config.json")) as f:
    config = json.load(f)




# Using the parsed arguments from config.json
processing_ins_type = config["processing_instance_type"]
processing_ins_count = config["processing_instance_count"]
training_ins_type = config["training_instance_type"]
model_approve_status = config["model_approval_status"]
processing_step_name = config["processing_step_name"]
model_path_name = config["model_path_name"]
TrainingStepName = config["TrainingStepName"]
RegisterModel_name = config["RegisterModel_name"]
ModelCreation_name = config["ModelCreation_name"]
Transformer_name = config["Transformer_name"] 
CheckMSEEvaluation_name = config["CheckMSEEvaluation_name"]
step_evaluation_name = config["step_evaluation_name"]
PreprocessData_name = config["PreprocessData_name"]
PipelineName = config["PipelineName"]
JobName = config["JobName"]
ModelPackageGroupName = config["ModelPackageGroupName"]
inference_instance_type = config["inference_instance_type"]
transform_instances_type = config["transform_instances_type"]
input_data_csv_file = config["input_data_csv_file"]
input_path_batch_libsvm = config["input_path_batch_libsvm"]
sklearn_framework_version = config["sklearn_framework_version"]

model_framework = config['image_uri']["model_framework"]
model_framework_version = config['image_uri']["model_framework_version"]
model_framework_py_version = config['image_uri']["model_framework_py_version"]

estimator_name = config['estimator']["estimator_name"]
estimator_objective = config['estimator']["estimator_objective"]
estimator_num_round = config['estimator']["estimator_num_round"]
estimator_max_depth = config['estimator']["estimator_max_depth"]
estimator_eta = config['estimator']["estimator_eta"]
estimator_gamma = config['estimator']["estimator_gamma"]
estimator_subsample = config['estimator']["estimator_subsample"]
estimator_silent = config['estimator']["estimator_silent"]
estimator_min_child_weight = config['estimator']["estimator_min_child_weight"]


condition_step_right = config['condition_step']['condition_step_right']
condition_step_json_path = config['condition_step']['condition_step_json_path']

batch_model_status = config['batch_model']['batch_model_status']
create_model_step_accelerator_type = config['create_model_step_accelerator_type']

EvaluateModel_name = config['Evaluation']["EvaluateModel_name"]
EvaluationReport_name = config['Evaluation']["EvaluationReport_name"]
Evaluation_output_name = config['Evaluation']["Evaluation_output_name"]
Evaluation_path = config['Evaluation']["Evaluation_path"]

base_path = config['base_path']



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
    model_package_group_name=ModelPackageGroupName,
    pipeline_name=PipelineName,
    base_job_prefix=JobName,
    docker_image=None,
    estimator=None,
    hyperparameters=None,
    custom_metrics=None,
    ):
    """Gets a SageMaker ML Pipeline instance working with on the data.

    Args:
        region: AWS region to create and run the pipeline.
        role: IAM role to create and run steps and pipeline.
        default_bucket: the bucket to use for storing the artifacts
        model: the name of the custom model to use. If None, uses the in-built model framework name's model.
        ~ In-built model will automatically get the docker image uri and place it in image_uri variable
        hyperparameters: Need estimators if custom trained model is provided with custom metrics


    Returns:
        an instance of a pipeline
    """
    sagemaker_session = get_session(region, default_bucket)
    if role is None:
        role = sagemaker.session.get_execution_role(sagemaker_session)

    
    ### parameters for pipeline execution
    processing_instance_type = ParameterString(name="ProcessingInstanceType", default_value=processing_ins_type)
    processing_instance_count = ParameterInteger(name="ProcessingInstanceCount", default_value=processing_ins_count)
    training_instance_type = ParameterString(name="TrainingInstanceType", default_value=training_ins_type)
    model_approval_status = ParameterString(name="ModelApprovalStatus", default_value=model_approve_status)
    model_framework_name = ParameterString(name="ModelFramework", default_value=model_framework)
    input_data = ParameterString( name="InputDataUrl",default_value=f"s3://sagemaker-project-p-qycqchvtg0ti/project/Consumer_Classification_Model_Sample_Records_for_Inference.csv",)
    # input_prefix = "s3://your-s3-bucket/sagemaker-project-p-qycqchvtg0ti/project/input_files"

    # Use an S3 prefix instead of a specific file name
    # input_data = ParameterString(name="InputDataUrl", default_value=input_prefix)


    s3 = boto3.resource('s3')
    input_path = "s3://sagemaker-project-p-qycqchvtg0ti/project/Modified_Consumer_Classification_Model_Sample_Records_for_Inference.csv"
    # batch_data = ParameterString(name="BatchData", default_value=input_path)
    # Use an S3 prefix instead of a specific file name
    input_prefix = "s3://your-s3-bucket/sagemaker-project-p-qycqchvtg0ti/project/inference_files/"
    batch_data = ParameterString(name="BatchData", default_value=input_prefix + "*")


    print('S3 input data file path for training :', "s3://sagemaker-project-p-qycqchvtg0ti/project/Consumer_Classification_Model_Sample_Records_for_Inference.csv")
    print('S3 batch data file path for batch :', input_path)


    # creates an instance of SKLearnProcessor step for feature engineering
    sklearn_processor = SKLearnProcessor(
        framework_version=sklearn_framework_version,
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/{processing_step_name}",
        sagemaker_session=sagemaker_session,
        role=role,
    )


    if os.path.exists(os.path.join(BASE_DIR, "preprocess.py")):
        step_process = ProcessingStep(
            name=PreprocessData_name,
            processor=sklearn_processor,
            outputs=[
                ProcessingOutput(output_name="train", source=f"{base_path}/train"),
                ProcessingOutput(output_name="validation", source=f"{base_path}/validation"),
                ProcessingOutput(output_name="test", source=f"{base_path}/test"),
            ],
            code=os.path.join(BASE_DIR, "preprocess.py"),
            job_arguments=[
                "--input-data", input_data,
                "--base_path", base_path,
            ],
        )
    else:
        # If preprocess.py file is not provided, we assume that the 
        # preprocessed data is stored in S3 as train.csv and validation.csv
        step_process = ProcessingStep(
            name=PreprocessData_name,
            processor=sklearn_processor,
            outputs=[
                ProcessingOutput(output_name="train", source=f"s3://{default_bucket}/{JobName}-train.csv"),
                ProcessingOutput(output_name="validation", source=f"s3://{default_bucket}/{JobName}-validation.csv"),
            ],
            job_arguments=[
                "--input-data", input_data,
                "--base_path", base_path
            ],
        )

  

    # training step for generating model artifacts
    model_path = f"s3://{sagemaker_session.default_bucket()}/{base_job_prefix}/{model_path_name}"

    print("Default Bucket:", default_bucket)
    print("IAM Role:", role)
    print("Model Path Name:", model_path_name)
    print("region :", region)


    if docker_image and hyperparameters:
        # Must define correct the uri of  docker image 
            image_uri = docker_image
            estimator = estimator_type(
                image_uri=image_uri,
                instance_type=training_instance_type,
                instance_count=processing_instance_count,
                output_path=model_path,
                base_job_name=f"{base_job_prefix}/{estimator_name}",
                sagemaker_session=sagemaker_session,
                region=region,
                role=role,)
            estimator.set_hyperparameters(**hyperparameters)
            
    else:

        # Retrieve the training script
        try:
            train_model_id, train_model_version, train_scope = "lightgbm-classification-model", "*", "training"
            training_instance_type = "ml.m5.xlarge"
            image_uri = image_uris.retrieve(
                region=None,
                framework=None,
                model_id=train_model_id,
                model_version=train_model_version,
                image_scope=train_scope,
                instance_type=training_instance_type,
                )
            print(' Lightgbm model ',image_uri)

            from sagemaker.estimator import Estimator
            from sagemaker import hyperparameters
           
            # Retrieve the training script
            train_source_uri = script_uris.retrieve(
                model_id=train_model_id, model_version=train_model_version, script_scope=train_scope
            )

            train_model_uri = model_uris.retrieve(
                model_id=train_model_id, model_version=train_model_version, model_scope=train_scope
            )

            # Retrieve the default hyperparameters for training the model
            hyperparameters = hyperparameters.retrieve_default(
                model_id=train_model_id, model_version=train_model_version
            )

            # [Optional] Override default hyperparameters with custom values
            hyperparameters[
                "num_boost_round"
            ] = "500"
            print(hyperparameters)
            estimator = Estimator(
                    role=role,
                        image_uri=image_uri,
                        source_dir=train_source_uri,
                        model_uri=train_model_uri,
                        entry_point="transfer_learning.py",
                        instance_count=1, 
                        instance_type=training_instance_type,
                        max_run=360000,
                        hyperparameters=hyperparameters,
                        output_path=model_path
                )
            


               
        except Exception as e:
            print('Current model framework ', model_framework)
            print(f"\n\nError occurred while retrieving built-in model: {e}")


    step_train = TrainingStep(
        name=TrainingStepName,
        estimator=estimator,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[
                    "validation"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )

    # processing step for evaluation
    script_eval = ScriptProcessor(
        image_uri=image_uri,
        command=["python3"],
        instance_type=processing_instance_type,
        instance_count=processing_instance_count,
        base_job_name=f"{base_job_prefix}/{step_evaluation_name}",
        sagemaker_session=sagemaker_session,
        role=role,
    )
    evaluation_report = PropertyFile(
        name = EvaluationReport_name,
        output_name=Evaluation_output_name,
        path=Evaluation_path,
    )


    step_eval = ProcessingStep(
        name=EvaluateModel_name,
        processor=script_eval,
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination=f"{base_path}/model",
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs[
                    "test"
                ].S3Output.S3Uri,
                destination=f"{base_path}/test",
            ),
        ],
        outputs=[
            ProcessingOutput(output_name="evaluation", source=f"{base_path}/evaluation"),
        ],
        code=os.path.join(BASE_DIR, "evaluate.py"),
        job_arguments=["--model-framework", model_framework], 
        property_files=[evaluation_report],
    )

    # register model step that will be conditionally executed
    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="{}/evaluation.json".format(
                step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
            ),
            content_type="application/json"
        )
    )
  
    ### register model step that will be conditionally executed
    if custom_metrics:
        model_metrics = ModelMetrics(custom_metrics)
    else:
        model_metrics = ModelMetrics(
            model_statistics=MetricsSource(
                s3_uri="{}/evaluation.json".format(
                    step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
                ),
                content_type="application/json"
            )
        )
    # Register the model
    step_register = RegisterModel(
        name=RegisterModel_name,
        estimator=estimator,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["text/csv"],
        response_types=["text/csv"],
        inference_instances=inference_instance_type,
        transform_instances=transform_instances_type,
        model_package_group_name=model_package_group_name,
        approval_status=model_approval_status,
        model_metrics=model_metrics,
    )

    # condition step for evaluating model quality and branching execution
    cond_lte = ConditionLessThanOrEqualTo(
        left=JsonGet(
            step=step_eval,
            property_file=evaluation_report,
            json_path=condition_step_json_path
        ),
        right=condition_step_right,
    )
    step_cond = ConditionStep(
        name=CheckMSEEvaluation_name,
        conditions=[cond_lte],
        if_steps=[step_register, ],
        else_steps=[],
    )


    ## Batch tranformation ########

    batch_model_approval_status = batch_model_status

    sm = boto3.client('sagemaker')
    response = sm.list_model_packages(
        ModelPackageGroupName=model_package_group_name,
        ModelApprovalStatus=batch_model_approval_status)
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
        name=ModelCreation_name,
        model=model,
        inputs=CreateModelInput(instance_type=inference_instance_type[1], accelerator_type=create_model_step_accelerator_type),
    )

  
    # Define the Transformer
    transformer = Transformer(
        model_name=create_model_step.properties.ModelName,
        instance_type=inference_instance_type[1],  
        instance_count=processing_instance_count,
        output_path=f"s3://{default_bucket}/{Transformer_name}",
        strategy='MultiRecord',
        assemble_with='Line',
        accept='text/csv',  # Set the content type to 'text/csv' for CSV input
    )
    # Define the TransformStep
    step_transform = TransformStep(
        name=Transformer_name,
        transformer=transformer,
        inputs=TransformInput(
            data="s3://your-s3-bucket/sagemaker-project-p-qycqchvtg0ti/project/inference_files/",
            content_type="text/csv", 
            split_type="Line",
            input_filter='$[1:]'
            ),
            
    )

    # Add dependencies of step_create_model and step_register to step_cond
    create_model_step.add_depends_on([step_register])
    step_transform.add_depends_on([create_model_step])

    # pipeline instance
    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            model_framework_name,
            processing_instance_type,
            processing_instance_count,
            training_instance_type,
            model_approval_status,
            batch_model_approval_status,
            input_data,
            batch_data
        ],
        steps=[step_process, step_train, step_eval, step_cond, create_model_step, step_transform],
        sagemaker_session=sagemaker_session,
    )
    return pipeline
