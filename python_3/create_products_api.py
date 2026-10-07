import boto3
from botocore.exceptions import ClientError


REGION = "us-east-1"
API_NAME = "ProductsApi"
LAMBDA_NAME = "ProductsLambda"
PRODUCTS_PATH = "items"
STAGE_NAME = "prod"

api_gateway = boto3.client("apigateway", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)
sts_client = boto3.client("sts", region_name=REGION)


def create_lambda_method(api_id, resource_id, http_method, integration_uri):
    api_gateway.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        authorizationType="NONE",
    )
    api_gateway.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod=http_method,
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=integration_uri,
    )


def create_api(lambda_arn):
    api_id = api_gateway.create_rest_api(
        name=API_NAME,
        description="CRUD API for computer products backed by DynamoDB.",
        endpointConfiguration={"types": ["REGIONAL"]},
    )["id"]

    resources = api_gateway.get_resources(restApiId=api_id)["items"]
    root_id = next(resource["id"] for resource in resources if resource["path"] == "/")
    items_resource_id = api_gateway.create_resource(
        restApiId=api_id,
        parentId=root_id,
        pathPart=PRODUCTS_PATH,
    )["id"]
    item_resource_id = api_gateway.create_resource(
        restApiId=api_id,
        parentId=items_resource_id,
        pathPart="{id}",
    )["id"]

    integration_uri = (
        f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/"
        f"{lambda_arn}/invocations"
    )

    for method in ("GET", "POST", "OPTIONS"):
        create_lambda_method(api_id, items_resource_id, method, integration_uri)
    for method in ("GET", "PUT", "DELETE", "OPTIONS"):
        create_lambda_method(api_id, item_resource_id, method, integration_uri)

    account_id = sts_client.get_caller_identity()["Account"]
    try:
        lambda_client.add_permission(
            FunctionName=LAMBDA_NAME,
            StatementId=f"AllowApiGateway-{api_id}",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/*/*",
        )
    except ClientError as error:
        if error.response["Error"]["Code"] != "ResourceConflictException":
            raise

    api_gateway.create_deployment(
        restApiId=api_id,
        stageName=STAGE_NAME,
    )
    api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/{STAGE_NAME}"
    print(f"Created API Gateway API: {api_id}")
    print(f"Set API_GW_BASE_URL_STR to: {api_url}")
    return api_url


if __name__ == "__main__":
    lambda_arn = lambda_client.get_function(
        FunctionName=LAMBDA_NAME
    )["Configuration"]["FunctionArn"]
    create_api(lambda_arn)
