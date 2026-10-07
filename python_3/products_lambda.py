import json
import os
from decimal import Decimal

import boto3


TABLE_NAME = os.environ.get("TABLE_NAME", "Products")
REGION = os.environ.get("AWS_REGION", "us-east-1")
table = boto3.resource("dynamodb", region_name=REGION).Table(TABLE_NAME)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Content-Type": "application/json",
}


def decimal_to_json(value):
    if isinstance(value, Decimal):
        return int(value) if value % 1 == 0 else float(value)
    raise TypeError(f"Unsupported value: {type(value).__name__}")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=decimal_to_json),
    }


def request_body(event):
    body = event.get("body") or "{}"
    return json.loads(body) if isinstance(body, str) else body


def product_id_from_event(event):
    value = (event.get("pathParameters") or {}).get("id")
    return int(value) if value is not None else None


def next_product_id():
    result = table.scan(ProjectionExpression="#id", ExpressionAttributeNames={"#id": "id"})
    ids = [int(item["id"]) for item in result.get("Items", [])]
    return max(ids, default=0) + 1


def lambda_handler(event, context):
    method = event.get("httpMethod", "GET").upper()
    product_id = product_id_from_event(event)

    if method == "OPTIONS":
        return response(204, {})

    try:
        if method == "GET":
            if product_id is not None:
                result = table.get_item(Key={"id": product_id})
                product = result.get("Item")
                return response(200, product) if product else response(404, {"message": "Product not found"})

            result = table.scan()
            return response(200, sorted(result.get("Items", []), key=lambda item: int(item["id"])))

        if method == "POST":
            body = request_body(event)
            if not body.get("name") or body.get("price") is None:
                return response(400, {"message": "name and price are required"})

            item = {
                "id": next_product_id(),
                "name": str(body["name"]),
                "price": Decimal(str(body["price"])),
            }
            table.put_item(Item=item, ConditionExpression="attribute_not_exists(id)")
            return response(201, item)

        if method == "PUT":
            if product_id is None:
                return response(400, {"message": "Product id is required"})

            body = request_body(event)
            if not body.get("name") or body.get("price") is None:
                return response(400, {"message": "name and price are required"})

            result = table.update_item(
                Key={"id": product_id},
                UpdateExpression="SET #product_name = :name, #product_price = :price",
                ExpressionAttributeNames={
                    "#product_name": "name",
                    "#product_price": "price",
                },
                ExpressionAttributeValues={
                    ":name": str(body["name"]),
                    ":price": Decimal(str(body["price"])),
                },
                ConditionExpression="attribute_exists(id)",
                ReturnValues="ALL_NEW",
            )
            return response(200, result["Attributes"])

        if method == "DELETE":
            if product_id is None:
                return response(400, {"message": "Product id is required"})

            table.delete_item(
                Key={"id": product_id},
                ConditionExpression="attribute_exists(id)",
            )
            return response(200, {"message": "Product deleted"})

        return response(405, {"message": "Method not allowed"})
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        return response(404, {"message": "Product not found"})
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        return response(400, {"message": str(error)})
    except Exception as error:
        print(f"Unhandled request error: {error}")
        return response(500, {"message": "Internal server error"})
