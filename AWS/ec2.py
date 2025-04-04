import os
from dotenv import load_dotenv
import logging
import boto3 
from mypy_boto3_ec2.client import EC2Client
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)
load_dotenv()


class EC2():
    def __init__(self, ec2: EC2Client, instance_ids: list[str]):
        self.ec2 = ec2
        self.instance_ids = instance_ids

    def start_instance(self, instance_id: str):
        # Do a dryrun first to verify permissions
        try:
            self.ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        # try:
        #     response = ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
        #     print(response)
        # except ClientError as e:
        #     print(e)

    def stop_instance(self, instance_id: str):
        # Do a dryrun first to verify permissions
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        # try:
        #     response = self.ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
        #     print(response)
        # except ClientError as e:
        #     print(e)

    def describe_instances(self):
        return self.ec2.describe_instances()

if __name__ == "__main__":
    instance_id = os.getenv('instance_id')
    if instance_id:
        ec2 = EC2(
            ec2=boto3.client('ec2'),
            instance_ids=[instance_id]
        )
        # print(ec2.describe_instances())
        ec2.start_instance("i-0e84e94476bf8680d")
