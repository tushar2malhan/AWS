"""Feature engineers the the dataset."""
import argparse
import logging
import os
import csv
import pathlib
import requests
import tempfile
import boto3
import json
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())


def merge_two_dicts(x, y):
    """Merges two dicts, returning a new copy."""
    z = x.copy()
    z.update(y)
    return z


if __name__ == "__main__":
    logger.debug("Starting preprocessing.")

    parser = argparse.ArgumentParser()
    parser.add_argument("--input-data", type=str, required=True)
    parser.add_argument("--base_path", type=str, required=True)
    args = parser.parse_args()

   
    base_dir = args.base_path
    pathlib.Path(f"{base_dir}/data").mkdir(parents=True, exist_ok=True)
    input_data = args.input_data

    bucket = input_data.split("/")[2]
    key = "/".join(input_data.split("/")[3:])
    input_data_csv_file = input_data.split('/')[-1]

    if input_data_csv_file.endswith('.csv'):
        print("The file name ends with '.csv'")
    else:
        print("The file name does not end with '.csv'")

    logger.info("Downloading data from bucket: %s, key: %s", bucket, key)
    fn = f"{base_dir}/data/{input_data_csv_file}"
    s3 = boto3.resource("s3")
    s3.Bucket(bucket).download_file(key, fn)
    print(f"File downloaded to {fn}")


    with open(fn, 'r') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader)

    feature_columns_names = headers[:-1]  # All headers except the last one as feature columns
    label_column = str(headers[-1])  # Last header as the label column
    
    print('features length', len(feature_columns_names))
    print('label ', label_column)

    feature_columns_dtype = {}

    for i, column in enumerate(feature_columns_names):
        feature_columns_dtype[column] = np.float64

    label_column_dtype = {label_column: np.float64}
 
    
    logger.debug("Reading downloaded data.")
    df = pd.read_csv(
        fn,
        skiprows=1,  # Exclude the header row
        names=feature_columns_names + [label_column]
    )
    #dtype=merge_two_dicts(feature_columns_dtype, label_column_dtype),
    os.unlink(fn)
    logger.info("First few rows of test data from PREPROCESS.PY:")
    logger.info(df.head())

    logger.debug("Defining transformers.")
    numeric_features = list(feature_columns_names)

    numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), 
        ("scaler", StandardScaler())]
    )

    # Defines transformers for preprocessing the numeric features. In this case, it uses SimpleImputer to handle missing values by replacing them with the median, and StandardScaler to scale the features.
    preprocess = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
        ]
    )

    logger.info("Applying transforms.")
    # The label column is separated from the DataFrame and stored in y
    y = df.pop(label_column)
    # The preprocessed feature columns are stored in X_pre.
    X_pre = preprocess.fit_transform(df)
    y_pre = y.to_numpy().reshape(len(y), 1)  # reshape the column as per the feature [1, feature_1, feature_2],


    # Concatenates the label column y_pre with the preprocessed feature columns X_pre to form the final preprocessed dataset X.
    X = np.concatenate((y_pre, X_pre), axis=1)  # input and output 

    # Writes out the train, validation, and test datasets as CSV files in the respective directories within the base_dir.
    logger.info("Splitting %d rows of data into train, validation, test datasets.", len(X))
    np.random.shuffle(X)
    train, validation, test = np.split(X, [int(0.7 * len(X)), int(0.85 * len(X))])

    logger.info("Writing out datasets to %s.", base_dir)
    pd.DataFrame(train).to_csv(f"{base_dir}/train/train.csv", header=False, index=False)
    pd.DataFrame(validation).to_csv(
        f"{base_dir}/validation/validation.csv", header=False, index=False
    )
    pd.DataFrame(test).to_csv(f"{base_dir}/test/test.csv", header=False, index=False)
