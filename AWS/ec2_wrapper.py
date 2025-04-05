import os
from dotenv import load_dotenv
import logging
import boto3 
from mypy_boto3_ec2.client import EC2Client
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
load_dotenv(override=True)

class EC2_Wrapper():
    def __init__(self, ec2: EC2Client):
        """
        Initializes the EC2 instance.

        :param ec2: A Boto3 EC2 client. This client provides low-level
                    access to AWS EC2 services.
        """
        self.ec2 = ec2

    def start_instance(self, instance_id: str):
        """
        Starts an AWS EC2 instance that matches instance_id. Performs a dry run
        to verify permissions. If successful, runs start_instances without a dry run.

        :param instance_id: The instance id of the EC2 instance to start.
        """
        # Do a dryrun first to verify permissions
        try:
            self.ec2.start_instances(InstanceIds=[instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        try:
            response = self.ec2.start_instances(InstanceIds=[instance_id], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    def stop_instance(self, instance_id: str):
        """
        Stops an AWS EC2 instance that matches instance_id. Performs a dry run
        to verify permissions. If successful, runs stop_instances without a dry run.

        :param instance_id: The instance id of the EC2 instance to stop.
        """
        # Do a dryrun first to verify permissions
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    def describe_instances(self):
        """
        Describes the AWS EC2 instances that exists for the user.

        :param instance_id: The instance id of the EC2 instance to stop.
        """
        return self.ec2.describe_instances()

if __name__ == "__main__":
    ec2 = EC2_Wrapper(
        ec2=boto3.client('ec2'),
    )
    
    instance_id = os.getenv('aws_instance_id')
    if instance_id:
        ec2.stop_instance(instance_id)
