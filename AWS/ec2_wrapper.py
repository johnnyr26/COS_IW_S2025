import os
from dotenv import load_dotenv
import logging
import boto3 
from datetime import datetime, timezone
from typing import Sequence
from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ec2.literals import InstanceTypeType
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
    
    def describe_spot_price_history(
        self,
        instance_types: Sequence[InstanceTypeType],
        start_time: datetime,
        end_time: datetime
    ):
        """
        Describes the spot price history for the particular EC2 instance

        :param instance_types: The list of instance types to fetch the spot prices for.
        :param start_time: the starting time to fetch the spot prices.
        :param end_time: the ending time to fetch the spot prices.
        :returns: dictionary of the instance, the spot price, and the timestamp.
        """
        response = self.ec2.describe_spot_price_history(
            EndTime=end_time,
            InstanceTypes=instance_types,
            ProductDescriptions=[
                'Linux/UNIX (Amazon VPC)',
            ],
            StartTime=start_time,
        )

        spot_prices: list[dict[str, str | datetime | None]] = []
        for data in response['SpotPriceHistory']:
            price = data.get('SpotPrice')
            instance_type = data.get('InstanceType')
            timestamp = data.get('Timestamp')
            if timestamp:
                timestamp = timestamp.now(timezone.utc)

            spot_prices.append({
                "instance": instance_type,
                "price": price,
                "timestamp": timestamp
            })

        return spot_prices
    


if __name__ == "__main__":
    ec2 = EC2_Wrapper(
        ec2=boto3.client('ec2'),
    )
    
    instance_id = os.getenv('aws_instance_id')
    if instance_id:
        end_time = datetime.now()
        start_time = end_time
        response = ec2.describe_spot_price_history(
            start_time=start_time,
            end_time=end_time,
            instance_types=["m4.large"]
        )
        print(response)
