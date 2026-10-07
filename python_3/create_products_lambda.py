import io
import zipfile
from pathlib import Path

import boto3


REGION = "us-east-1"
LAMBDA_NAME = "ProductsLambda"
ROLE_ARN = "<FMI_ROLE_ARN>"

lambda_client = boto3.client("lambda", region_name=REGION)


def lambda_zip():
    handler_path = Path(__file__).with_name("products_lambda.py")
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        package.write(handler_path, arcname="products_lambda.py")
    return archive.getvalue()


def create_or_update_lambda():
    if ROLE_ARN.startswith("<FMI"):
        raise ValueError("Replace ROLE_ARN with the Lambda execution role ARN first")

    code = lambda_zip()
    try:
        function = lambda_client.get_function(FunctionName=LAMBDA_NAME)
        lambda_client.update_function_code(
            FunctionName=LAMBDA_NAME,
            ZipFile=code,
            Publish=True,
        )
        lambda_client.update_function_configuration(
            FunctionName=LAMBDA_NAME,
            Role=ROLE_ARN,
            Runtime="python3.12",
            Handler="products_lambda.lambda_handler",
            Environment={"Variables": {"TABLE_NAME": "Products"}},
        )
        print(f"Updated Lambda function: {LAMBDA_NAME}")
        return function["Configuration"]["FunctionArn"]
    except lambda_client.exceptions.ResourceNotFoundException:
        function = lambda_client.create_function(
            FunctionName=LAMBDA_NAME,
            Runtime="python3.12",
            Role=ROLE_ARN,
            Handler="products_lambda.lambda_handler",
            Code={"ZipFile": code},
            Publish=True,
            Environment={"Variables": {"TABLE_NAME": "Products"}},
            Description="CRUD Lambda for the computer products DynamoDB table",
        )
        print(f"Created Lambda function: {LAMBDA_NAME}")
        return function["FunctionArn"]


if __name__ == "__main__":
    create_or_update_lambda()
