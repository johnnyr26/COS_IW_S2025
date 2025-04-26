import boto3
from boto3.dynamodb.types import TypeSerializer
from typing import Any

class DynamoDB_Wrapper:
    def __init__(self, table_name: str, partition_key: str):
        """
        Initializes the DynamoDB instance.

        :param table_name: The name of the table to insert the item.
        :param partition_key: The partition key for the table.
        """
        self.dynamo_db = boto3.client("dynamodb")
        self.table_name = table_name
        self.partition_key = partition_key

    def put_item(self, id: int, item: dict[str, Any]):
        """
        Puts an item to the database.
            Raises a ConditionalCheckFailedException if the item exists already.

        :param id: the value of the partition_key
        :param item: the item to put to the database.
        :returns: PutItem response metadata
        """
        try:
            item["id"] = str(id)

            # serializes all of the items to be uploaded to DynamoDB
            serializer = TypeSerializer()
            dynamo_item = {key: serializer.serialize(val) for key, val in item.items()}

            response = self.dynamo_db.put_item(
                TableName=self.table_name,
                Item=dynamo_item,
                ConditionExpression=f'attribute_not_exists({self.partition_key})'
            )

            if response["ResponseMetadata"].get("HTTPStatusCode") != 200:
                raise Exception(f"Failed to upload item for ID {id}")

            prev_id = self.get_highest_id()
            if prev_id < int(item['id']):
                # this makes it easier to keep track of the latest item
                self.dynamo_db.put_item(
                    TableName=self.table_name,
                    Item={
                        'id': {
                            'S': 'latest_id',
                        },
                        'latest': {
                            'S': item['id']
                        }
                    },
                )
            return response
        except Exception as ex:
            print(ex)
            raise ex

    def get_highest_id(self) -> int:
        try:
            response = self.get_item(key="latest_id")
            if response:
                if 'Item' in response and 'latest' in response['Item']:
                    if 'S' in response['Item']['latest']:
                        return int(response['Item']['latest']['S'])
                    raise KeyError("Key 'S' not found in the response['Item']['latest']")
            return 0
        except Exception:
            return 0    


    def get_item_count(self) -> int:
        """
        Gets the number of items in the table.
            Note, the value updates every 6 hours. 

        :returns: Number of items in the table.
        """
        return self.dynamo_db.describe_table(TableName=self.table_name).get('Table', {}).get('ItemCount', 0)

    def get_item(self, key: str):
        """
        Retrieves an item from the table.

        :param key: The key of the item to retrieve.
        :returns: The retrieved item as a dictionary.
        """
        return self.dynamo_db.get_item(TableName=self.table_name, Key={self.partition_key: {'S': key}})


if __name__ == "__main__":
    dynamo_db = DynamoDB_Wrapper('wikipedia_table', 'id')
    print(dynamo_db.put_item(id=1, item={"url": "abc", "content": "a"}))
    print(dynamo_db.get_item_count())
