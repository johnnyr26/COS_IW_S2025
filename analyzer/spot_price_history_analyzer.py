import os
import csv
import heapq
import boto3
from dotenv import load_dotenv
from datetime import datetime, timedelta
from AWS.ec2_wrapper import EC2_Wrapper
from Azure.vm_wrapper import Azure_VM_Wrapper


load_dotenv(override=True)


class Spot_Price_History_Analyzer:
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

        print("Azure spot price history", azure_spot_price_history)

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

            timestamp_of_switches: list[datetime] = []

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

                #  track number of switches between VM's
                if curr_vm != "" and curr_vm != selected_vm:
                    timestamp_of_switches.append(spot_price.timestamp)
                    switches += 1

                curr_vm = selected_vm
                curr_price = selected_price

                spot_price_log.append(
                    {
                        "vm_type": curr_vm,
                        "timestamp": spot_price.timestamp,
                        "price": curr_price,
                        "aws_price": curr_aws_price,
                        "azure_price": curr_azure_price
                    }
                )

            return spot_price_log, switches, timestamp_of_switches

    # def calculate_aws_cost(
    #     self, aws_instance: str, start_time: datetime, end_time: datetime
    # ):
    #     spot_price_history = self.aws.get_spot_price_history(
    #         vm_type=aws_instance, start_time=start_time, end_time=end_time
    #     )

    #     if len(spot_price_history) > 1:
    #         total_cost = 0
    #         for i in range(1, len(spot_price_history)):
    #             seconds_elasped = abs((
    #                 spot_price_history[i].timestamp
    #                 - spot_price_history[i - 1].timestamp
    #             ).total_seconds())

    #             price_rate = spot_price_history[i - 1].price / 3600

    #             total_cost += (price_rate * seconds_elasped)

    #         return total_cost

    # def calculate_azure_cost(
    #     self, azure_vm: str, start_time: datetime, end_time: datetime
    # ):
    #     spot_price_history = self.azure.get_spot_price_history(
    #         vm_type=azure_vm, start_time=start_time, end_time=end_time, region="eastus"
    #     )

    #     seconds_elasped = (end_time - start_time).total_seconds()
    #     price_rate = spot_price_history[0].price / 3600

    #     total_cost = (price_rate * seconds_elasped)

    #     return total_cost

    # def calculate_total_cost(
    #     self, spot_price_log: list[dict[str, datetime | str | float]]
    # ):
    #     if len(spot_price_log) > 1:
    #         total_cost = 0
    #         for i in range(1, len(spot_price_log)):
    #             seconds_elapsed = abs((
    #                 spot_price_log[i]["timestamp"] - spot_price_log[i - 1]["timestamp"]
    #             ).total_seconds())
    #             # divides the hourly price rate to seconds.
    #             price_rate = spot_price_log[i - 1]["price"] / 3600

    #             total_cost += (price_rate * seconds_elapsed)

    #         return total_cost

    def create_csv(
        self,
        filename: str,
        spot_price_log: list[dict[str, datetime | str | float]],
    ):
        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=["vm_type", "timestamp", "price", "aws_price", "azure_price"]
            )
            writer.writeheader()
            writer.writerows(spot_price_log)

    def analyze_switch_logs(
        self,
        switch_logs: list[dict[str, str | int]],
        timestamp_of_switches: list[list[datetime]],
    ) -> dict[str, float | timedelta]:
        switches = list(
            log["switches"] for log in switch_logs if isinstance(log["switches"], int)
        )

        if len(switch_logs) == 0:
            return {}

        avg_switches = sum(switches) / len(switch_logs)
        max_switches = max(switches) if switches else 0
        min_switches = min(switches) if switches else 0

        avg_timedelta = timedelta(0)
        total_timestamps = 0
        total_switch_timedelta = timedelta(0)

        for timestamps in timestamp_of_switches:
            if len(timestamps) > 1:
                switch_timedelta = timedelta(0)
                total_timestamps += len(timestamps) - 1
                for i in range(1, len(timestamps)):
                    switch_timedelta += abs(timestamps[i] - timestamps[i - 1])
                total_switch_timedelta += switch_timedelta

        if total_timestamps > 0:
            avg_timedelta = total_switch_timedelta / total_timestamps

        return {
            "avg_switches": avg_switches,
            "max_switches": max_switches,
            "min_switches": min_switches,
            "avg_timedelta": avg_timedelta,
        }

    def analyze_spot_price_history(self):
        pass
        # end_time = datetime.now()
        # start_time = end_time - timedelta(days=7)

        # vcpus = [192]
        # memories = [2048]

        # switch_logs: list[dict[str, str | int]] = []
        # switches_timestamps: list[list[datetime]] = []

        # for vcpu in vcpus:
        #     for memory in memories:

        #         aws_instances = self.aws.find_matching_instance_types(
        #             vcpus=vcpu, memory=memory
        #         )
        #         azure_vms = self.azure.find_matching_vm_types(vcpus=vcpu, memory=memory)

        #         max_switches = 0
        #         champ_log = None
        #         champ_aws = None
        #         champ_azure = None

        #         for aws_instance in ["p4d.24xlarge"]:
        #             for azure_vm in ["Standard_NC6s_v3"]:
        #                 result = analyzer.compare_costs(
        #                     aws_instance=aws_instance,
        #                     azure_vm=azure_vm,
        #                     start_time=start_time,
        #                     end_time=end_time,
        #                 )

        #                 if result:
        #                     spot_log, switches, timestamp_of_switches = result

        #                     if switches > 1:

        #                         switch_logs.append(
        #                             {
        #                                 "aws_instance": aws_instance,
        #                                 "azure_vm": azure_vm,
        #                                 "switches": switches,
        #                             }
        #                         )

        #                         switches_timestamps.append(timestamp_of_switches)

        #                         # if switches > max_switches:
        #                     champ_log = spot_log
        #                     champ_aws = aws_instance
        #                     champ_azure = azure_vm
        #                     # max_switches = switches

        #         # print(switch_logs)
        #         # print(analyzer.analyze_switch_logs(switch_logs=switch_logs, timestamp_of_switches=switches_timestamps))

        #         if champ_log:
        #             print("AWS INSTANCE", champ_aws)
        #             print("Azure INSTANCE", champ_azure)
        #             print("TOTAL COST", analyzer.calculate_total_cost(champ_log))
        #             print(
        #                 "AWS COST",
        #                 analyzer.calculate_aws_cost(
        #                     champ_aws, start_time=start_time, end_time=end_time
        #                 ),
        #             )
        #             print(
        #                 "Azure COST",
        #                 analyzer.calculate_azure_cost(
        #                     champ_azure,
        #                     start_time=start_time,
        #                     end_time=end_time
        #                 ),
        #             )

        #             analyzer.create_csv(
        #                 f"{champ_aws},{champ_azure},{vcpu}vcpus_{memory}GiB.csv",
        #                 spot_price_log=champ_log,
        #             )
    

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
        ec2 = EC2_Wrapper()
        analyzer = Spot_Price_History_Analyzer(aws=ec2, azure=azure)



        


# Azure: D2 v4, 2vCPU and 8GiB
# AWS: m4.large, 2vCPU and 8GiB