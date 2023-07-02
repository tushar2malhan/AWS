"""Evaluation script for measuring mean squared error."""
import os
import argparse
import json
import logging
import pathlib
import pickle
import tarfile
import joblib

import numpy as np
import pandas as pd
# import xgboost

import subprocess

# Define the command to install LightGBM using pip
command = ['pip', 'install', 'lightgbm']

# Execute the command using subprocess
try:
    subprocess.check_call(command)
    print("LightGBM installed successfully!")
except subprocess.CalledProcessError as e:
    print("An error occurred while installing LightGBM:", e)

import lightgbm as lgb

from sklearn.metrics import mean_squared_error

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())



if __name__ == "__main__":
    logger.debug("Starting evaluation.")
    model_path = "/opt/ml/processing/model/model.tar.gz"
    # with tarfile.open(model_path) as tar:
    #     tar.extractall(path=".")
    with tarfile.open(model_path, 'r:gz') as tar:
        tar.extractall()
    # The script starts by extracting the model artifacts from the model.tar.gz file. The model artifacts are assumed to be located at /opt/ml/processing/model/ within the processing environment.'
        member_names = tar.getnames()
        print(member_names)

        # Assuming the serialized model file has a ".pkl" extension
        # Find the file with the ".pkl" extension in the member names
        model_file_path = next((name for name in member_names if name.endswith('.pkl')), None)

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-framework", type=str, required=True)
    args = parser.parse_args()
    model_framework_name = args.model_framework


    # model = pickle.load(open(f"{model_framework_name}-model", "rb"))
    logger.debug(f"Loading {model_framework_name} model.")

    if model_framework_name == "lightgbm":
        # model = lgb.Booster(model_file=f"{model_framework_name}-model")
        print('Loading model ', model_framework_name)
        # model_file_path = f"{model_framework_name}-model.txt"
        model = joblib.load(model_file_path)
    else:
        model = pickle.load(open(f"{model_framework_name}-model", "rb"))


    # The script reads the test data from the test.csv file, assumed to be located at /opt/ml/processing/test/ within the processing environment. The data is loaded into a pandas DataFrame (df).
    logger.debug("Reading test data.")
    test_path = "/opt/ml/processing/test/test.csv"
    df = pd.read_csv(test_path, header=None)


    # the target variable y_test is extracted from the last column (df.iloc[:, -1]) of the DataFrame df. The last column is then dropped from df using df.drop(df.columns[-1], axis=1, inplace=True). The remaining columns are considered as input features for evaluation.
    logger.debug("Reading test data.")
    y_test = df.iloc[:, -1].to_numpy() #  It retrieves the values of the target variable.This converts the selected column of the DataFrame to a NumPy array. It returns the target variable values as a NumPy array.
    df.drop(df.columns[-1], axis=1, inplace=True) # This drops the last column from the DataFrame along the column axis (axis=1). It removes the column from the DataFrame. # modification is made directly on the DataFrame df itself, without creating a new DataFrame.# modified DataFrame no longer contains the Target column.
    
    print('Current model framework name', model_framework_name)
    
    # X_test = eval(model_framework_name).DMatrix(df.values)
    X_test = lgb.Dataset(df.values) if model_framework_name =='lightgbm' else xgboost.DMatrix(df.values)

    logger.info("Performing predictions against test data.")

    print('X test data', X_test.data)

    ### if using model  lightgbm model
    predictions = model.predict(X_test.data)

    ### ### if using model  xgboost model
    # predictions = model.predict(X_test)

    # mean_squared_error(y_test, predictions) calculates the mean squared error between the true values (y_test) and the predicted values (predictions). The mean squared error is a commonly used metric to evaluate the performance of regression models. It measures the average squared difference between the predicted and true values. The result is stored in the variable mse.
    
    logger.debug("Calculating mean squared error.")
    mse = mean_squared_error(y_test, predictions)
    std = np.std(y_test - predictions)
    report_dict = {
        "regression_metrics": {
            "mse": {
                "value": mse,
                "standard_deviation": std
            },
        },
    }

    output_dir = "/opt/ml/processing/evaluation"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Writing out evaluation report with mse: %f", mse)
    evaluation_path = f"{output_dir}/evaluation.json"
    with open(evaluation_path, "w") as f:
        f.write(json.dumps(report_dict))
