from mypy_boto3_s3.client import S3Client

class S3_Wrapper():
    def __init__(self, s3: S3Client):
        self.s3 = s3
    
    def upload_file(self, filename: str, bucket: str, key: str):
        self.s3.upload_file(filename, bucket, key)