import boto3
from mypy_boto3_dynamodb.client import DynamoDBClient
from botocore.exceptions import ClientError

class DynamoDBWrapper:
    def __init__(self, dynamo_db: DynamoDBClient, table_name: str, partition_key: str):
        """
        Initializes the DynamoDB instance.

        :param dynamo_db: A Boto3 DynamoDB client. This client provides low-level
                    access to AWS DynamoDB services.
        :param table_name: The name of the table to insert the item.
        :param partition_key: The partition key for the table.
        """
        self.dynamo_db = dynamo_db
        self.table_name = table_name
        self.partition_key = partition_key

    def put_item(self, id: str, item: str):
        """
        Puts an item to the database.
        Raises a ConditionalCheckFailedException if the item exists already.

        :param id: the value of the partition_key
        :param item: the item to put to the database.
        :returns: PutItem response metadata
        """
        try:
            response = self.dynamo_db.put_item(
                TableName=self.table_name,
                Item={self.partition_key: {'S': id}, 'web_content': {'S': item}},
                ConditionExpression=f'attribute_not_exists({self.partition_key})'
            )
            return response
        except ClientError as ex:
            raise ex

if __name__ == "__main__":
    dynamo_db = DynamoDBWrapper(boto3.client('dynamodb'), 'COS_IW_TABLE', 'website_id')
    print(dynamo_db.put_item(id="2", item="This is a second example."))
