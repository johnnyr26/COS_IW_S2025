import boto3
from mypy_boto3_s3.client import S3Client

class S3_Wrapper():
    def __init__(self, s3: S3Client):
        """
        Initializes the S3 client.

        :param ssm: A Boto3 SSM client. This client allows user to upload
                        files to an S3 bucket for storage.
        """
        self.s3 = s3
    
    def upload_file(self, filepath: str, bucket: str, key: str):
        """
        Uploads the file to the s3 storage. 

        :param filenmae: The name of the file to be uploaded.
        :param bucket: The name of the bucket to store the file.
        :param key: The unique name to identify the file in the bucket.
        """
        self.s3.upload_file(filepath, bucket, key)

if __name__ == "__main__":
    s3 = S3_Wrapper(boto3.client("s3"))
    s3.upload_file("AWS/hello_world.sh", "johnrmrzbucket", "hello_world.sh")