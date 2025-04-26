import os
from dotenv import load_dotenv
import logging
import boto3
from datetime import datetime, timezone, timedelta
from mypy_boto3_ec2.client import EC2Client
from mypy_boto3_ec2.literals import InstanceTypeType
from botocore.exceptions import ClientError

from shared.virtual_machine import Virtual_Machine
from shared.types.spot_price import Spot_Price

logger = logging.getLogger(__name__)
load_dotenv(override=True)

MiB_MULTIPLIER = 1024


class EC2_Wrapper(Virtual_Machine):
    def __init__(self):
        """
        Initializes the EC2 instance.

        :param ec2: A Boto3 EC2 client. This client provides low-level
                    access to AWS EC2 services.
        """
        self.ec2 = boto3.client("ec2")

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
            if "DryRunOperation" not in str(e):
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
            if "DryRunOperation" not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = self.ec2.stop_instances(InstanceIds=[instance_id], DryRun=False)
            print(response)
        except ClientError as e:
            print(e)

    def find_matching_instance_types(self, vcpus: int, memory: int) -> list[str]:
        """
        Finds all instance types that matches the vCPUS and memory.

        :param vcpus: the amount of vCPUs that each instance must match.
        :param memory: the amount of memory (GiB) that each instance must match
        :returns: list of all EC2 instance types that matches the vCPUs and memory.
        """

        # Paginate through all instance types
        paginator = self.ec2.get_paginator("describe_instance_types")
        page_iterator = paginator.paginate()

        matching_instance_types: list[str] = []

        for page in page_iterator:
            for instance in page["InstanceTypes"]:
                instance_vcpus = instance.get("VCpuInfo", {}).get("DefaultVCpus")
                if instance_vcpus is None:
                    continue
                memory_info = instance.get("MemoryInfo")
                if memory_info and "SizeInMiB" in memory_info:
                    memory_mib = memory_info["SizeInMiB"]

                    if (
                        instance_vcpus == vcpus
                        and memory_mib == memory * MiB_MULTIPLIER
                    ):
                        instance_type = instance.get("InstanceType")
                        supports_spot = "spot" in instance.get(
                            "SupportedUsageClasses", []
                        )
                        if instance_type and supports_spot:
                            matching_instance_types.append(instance_type)

        return matching_instance_types

    def get_spot_price(
        self,
        vm_type: str | InstanceTypeType | None = None,
        vm_name: str | None = None,
        region: str | None = None,
    ) -> Spot_Price | None:
        """
        Describes the current spot price for the particular EC2 instance

        :param vm_type: The EC2 instance type to fetch the spot price.
        :param region: the availability zone of the EC2 instance.
        :returns: current spot price of the EC2 instance for that particular region
        """

        start_time = end_time = datetime.now()

        response = None

        if vm_name:
            instances = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [vm_name]}
                ]
            )

            # Get the instance type and AZ
            reservations = instances.get('Reservations', [])
            if not reservations or 'Instances' not in reservations[0]:
                raise ValueError("No instances found in the response.")
            instance_info = reservations[0]['Instances'][0]
            instance_type = instance_info.get('InstanceType')
            response = self.ec2.describe_spot_price_history(
                EndTime=end_time,
                InstanceTypes=[instance_type],  # type: ignore
                ProductDescriptions=[
                    "Linux/UNIX (Amazon VPC)",
                ],
                AvailabilityZone=region if region else "",
                StartTime=start_time,
            )
        else:
            response = self.ec2.describe_spot_price_history(
                EndTime=end_time,
                InstanceTypes=[vm_type],  # type: ignore
                ProductDescriptions=[
                    "Linux/UNIX (Amazon VPC)",
                ],
                AvailabilityZone=region if region else "",
                StartTime=start_time,
            )

        spot_price_history = response.get("SpotPriceHistory", {})

        # just selects the first one since it offers different
        # availability zones within the same region.
        instance_type = spot_price_history[0].get("InstanceType")
        price = spot_price_history[0].get("SpotPrice")
        timestamp = spot_price_history[0].get("Timestamp")

        if timestamp:
            timestamp = timestamp.now(timezone.utc)

        if price:
            price = float(price)

        if instance_type and price and timestamp:
            spot_price = Spot_Price(
                vm_type=instance_type, price=price, timestamp=timestamp
            )
            return spot_price

    def get_spot_price_history(
        self,
        vm_type: str | InstanceTypeType,
        start_time: datetime,
        end_time: datetime,
        region: str | None = None,
    ) -> list[Spot_Price] | None:
        """
        Describes the spot price history for the particular EC2 instance

        :param instance_types: The list of instance types to fetch the spot prices for.
        :param start_time: the starting time to fetch the spot prices.
        :param region: the availability zone of the EC2 instance.
        :param end_time: the ending time to fetch the spot prices.
        :returns: list of Spot price instances.
        """
        response = self.ec2.describe_spot_price_history(
            EndTime=end_time,
            InstanceTypes=[vm_type],  # type: ignore
            ProductDescriptions=[
                "Linux/UNIX (Amazon VPC)",
            ],
            AvailabilityZone=region if region else "",
            StartTime=start_time,
        )

        spot_prices: list[Spot_Price] = []
        for data in response["SpotPriceHistory"]:
            price = data.get("SpotPrice")
            instance_type = data.get("InstanceType")
            timestamp = data.get("Timestamp")

            if timestamp:
                timestamp = timestamp.replace(tzinfo=timezone.utc)

            if price:
                price = float(price)

            if instance_type and price and timestamp:
                spot_price = Spot_Price(
                    vm_type=instance_type, price=price, timestamp=timestamp
                )
                spot_prices.append(spot_price)

        return spot_prices


if __name__ == "__main__":
    ec2 = EC2_Wrapper()
    print(ec2.find_matching_instance_types(vcpus=192, memory=2048))

    # instance_id = os.getenv("aws_instance_id")
    # if instance_id:
    #     end_time = datetime.now()
    #     start_time = end_time - timedelta(days=3)
    #     response = ec2.get_spot_price(
    #         vm_type="m4.large",
    #     )
    #     print(response)
