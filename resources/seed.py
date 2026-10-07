import json
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError


REGION = "us-east-1"
TABLE_NAME = "Products"


def create_table():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "N"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Created DynamoDB table: {TABLE_NAME}")
    except ClientError as error:
        if error.response["Error"]["Code"] == "ResourceInUseException":
            print(f"DynamoDB table already exists: {TABLE_NAME}")
        else:
            raise


def batch_put(products):
    dynamodb = boto3.resource("dynamodb", region_name=REGION)
    table = dynamodb.Table(TABLE_NAME)
    with table.batch_writer() as batch:
        for product in products:
            item = {
                "id": int(product["id"]),
                "name": product["name"],
                "price": Decimal(str(product["price"])),
            }
            batch.put_item(Item=item)
            print("Added product:", item["id"], item["name"])

if __name__ == '__main__':
    create_table()

    with open("resources/website/products.json") as json_file:
        products = json.load(json_file)

    batch_put(products)

