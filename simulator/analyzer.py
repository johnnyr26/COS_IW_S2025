import os
import csv
import heapq
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta
from AWS.ec2_wrapper import EC2_Wrapper
from Azure.vm_wrapper import Azure_VM_Wrapper


load_dotenv(override=True)


class Analzyer:
    def __init__(self, aws: EC2_Wrapper, azure: Azure_VM_Wrapper):
        self.aws = aws
        self.azure = azure

    def start_simulation(self):
        pass

    def compare_costs(
        self, aws_instance: str, azure_vm: str, start_time: datetime, end_time: datetime
    ):
        aws_spot_price_history = self.aws.get_spot_price_history(
            vm_type=aws_instance, start_time=start_time, end_time=end_time
        )
        azure_spot_price_history = self.azure.get_spot_price_history(
            vm_type=azure_vm, start_time=start_time, end_time=end_time, region="eastus"
        )

        if aws_spot_price_history and azure_spot_price_history:
            spot_price_histories = [*aws_spot_price_history, *azure_spot_price_history]
            spot_price_heap = [
                (spot_price.timestamp, spot_price)
                for spot_price in spot_price_histories
            ]
            heapq.heapify(spot_price_heap)
            switches = 0

            curr_vm = ""
            curr_aws_price = float("inf")
            curr_azure_price = float("inf")
            curr_price = float("inf")
            spot_price_log: list[dict[str, datetime | str | float]] = []

            while spot_price_heap:
                _, spot_price = heapq.heappop(spot_price_heap)

                if spot_price.vm_type == aws_instance:
                    curr_aws_price = spot_price.price
                else:
                    curr_azure_price = spot_price.price

                if curr_aws_price < curr_azure_price:
                    selected_vm = aws_instance
                    selected_price = curr_aws_price
                else:
                    selected_vm = azure_vm
                    selected_price = curr_azure_price

                # Count switch if selected VM is different from last
                if curr_vm != "" and curr_vm != selected_vm:
                    switches += 1

                curr_vm = selected_vm
                curr_price = selected_price

                spot_price_log.append(
                    {
                        "vm_type": curr_vm,
                        "timestamp": spot_price.timestamp,
                        "price": curr_price,
                    }
                )

            return spot_price_log

    def create_csv(
        self,
        filename: str,
        spot_price_log: list[dict[str, datetime | str | float]],
    ):
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=["vm_type", "timestamp", "price"]
            )
            writer.writeheader()
            writer.writerows(spot_price_log)


if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    container_name = os.getenv("azure_container_name")
    storage_name = os.getenv("azure_storage_name")
    instance_id = os.getenv("aws_instance_id")
    if (
        subscription_id
        and resource_group_name
        and vm_name
        and container_name
        and storage_name
        and instance_id
    ):
        azure = Azure_VM_Wrapper(subscription_id, resource_group_name)
        ec2 = EC2_Wrapper(ec2=boto3.client("ec2"))
        analyzer = Analzyer(aws=ec2, azure=azure)

        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        spot_price_log = analyzer.compare_costs(
            aws_instance="m6i.2xlarge",
            azure_vm="Standard_D32pls_v5",
            start_time=start_time,
            end_time=end_time,
        )

        if spot_price_log:
            analyzer.create_csv("standard.csv", spot_price_log=spot_price_log)

        # analyzer.compare_costs(aws_instance="m6i.2xlarge", azure_vm="Standard_D8s_v5", start_time=start_time, end_time=end_time)
