import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import RunCommandInput, RunCommandResult

# from storage_wrapper import Storage_Wrapper
from shared.virtual_machine import Virtual_Machine
from shared.types.spot_price import Spot_Price

load_dotenv(override=True)


class Azure_VM_Wrapper(Virtual_Machine):
    def __init__(self, subscription_id: str, resource_group_name: str):
        """
        Initializes the Azure VM Wrapper with the necessary credentials and subscriptions.
        Authenticates to the Azure account and creates a ComputeManageClient that provides
        low-level access to the virtual machines.

        :param subscription_id: the subscription id for the virtual machines.
        :param resource_group_name: the resource group name attached to the subscription.
        """
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(credential, subscription_id)

    def describe_vms(self):
        """
        Lists and describes all of the virtual machines belonging to the subscription
        and resource group.
        """
        vms = self.compute_client.virtual_machines.list(self.resource_group_name)
        for vm in vms:
            print(f"VM Name: {vm.name}")
            print(f"Resource Group: {resource_group_name}")
            print(f"Location: {vm.location}")
            if vm.storage_profile and vm.storage_profile.os_disk:
                print(f"Operating System: {vm.storage_profile.os_disk.os_type}")
            else:
                print("Operating System: Not available")

    def start_vm(self, vm_name: str):
        """
        Starts a virtual machine.

        :param vm_name: the name of the virtual machine to start.
        """
        start_vm_poller = self.compute_client.virtual_machines.begin_start(
            self.resource_group_name, vm_name
        )
        start_vm_poller.result()
        print(f"VM {vm_name} started")

    def stop_vm(self, vm_name: str):
        """
        Terminates a virtual machine.

        :param vm_name: the name of the virtual machine to terminate.
        """
        stop_vm_poller = self.compute_client.virtual_machines.begin_power_off(
            self.resource_group_name, vm_name
        )
        stop_vm_poller.result()
        print(f"VM {vm_name} terminated")

    def execute_commands(self, vm_name: str, commands: list[str]):
        """
        Executes a command on the virtual machine.

        :param vm_name: the name of the virtual machine to execute the command.
        :param commands: the list of commands to exceute on the virtual machine.
        """

        command_input = RunCommandInput(command_id="RunShellScript", script=commands)

        exec_command_poller = self.compute_client.virtual_machines.begin_run_command(  # type: ignore
            resource_group_name=self.resource_group_name,
            vm_name=vm_name,
            parameters=command_input,  # type: ignore
        )

        result = exec_command_poller.result()  # type: ignore

        if isinstance(result, RunCommandResult) and isinstance(result.value, list):
            for message in result.value:
                print(message.code)
                print(message.message)

    def get_spot_price_history(
        self,
        vm_type: str,
        start_time: datetime,
        end_time: datetime,
        region: str | None = None,
    ) -> list[Spot_Price] | None:
        """
        Fetches the spot price history for a particular Azure virtual machine.
        Uses the cloudprice API to fetch the prices from the past 30 days.

        :param vm_type: the VM name.
        :param start_time: the starting time for the spot price history.
        :param end_time: the ending time for the spot price history.
        :param region: the region of the VM.
        :returns: a list of spot prices for the date range (max 30-days).
        """
        url = f"https://data.cloudprice.net/api/v1/price_history_vm"
        params = {
            "vmname": vm_type,
            "currency": "USD",
            "timerange": "allAvailableTime",
            "tier": "spot",
            "payment": "payasyougo",
        }

        if region:
            params["regions"] = region

        headers = {
            # Request headers
            "Cache-Control": "no-cache",
            "subscription-key": os.getenv("cloudnet_subscription_primary_key", ""),
            "allowed-origins": "*",
        }

        spot_prices: list[Spot_Price] = []

        response = requests.get(url=url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            history_price_values = data.get("listHistoryPriceValues", {})
            for data in history_price_values:
                timestamp = datetime.strptime(
                    data.get("modifiedDate"), "%Y-%m-%d %H:%M:%S"
                )
                if timestamp < start_time or timestamp > end_time:
                    # filter out timestamps that do not fit within the bounds.
                    continue

                vm = data.get("name")
                price = data.get("linuxPrice")

                if price:
                    price = float(price)

                if timestamp:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                if vm and price and timestamp:
                    spot_price = Spot_Price(
                        vm_type=vm, price=price, timestamp=timestamp
                    )

                    spot_prices.append(spot_price)
            return spot_prices

    def get_spot_price(
        self, vm_type: str, region: str | None = None
    ) -> Spot_Price | None:
        """
        Fetches the current spot price for a particular Azure instance.
        Since the spot prices update periodically, fetching the most recent
        posted spot price will be used as the 'current' spot price.

        :param vm_type: the VM type to fetch the price for.
        :param region: the region of the VM.
        :returns: the most recently posted Spot Price.
        """

        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)

        spot_prices = self.get_spot_price_history(
            vm_type=vm_type, start_time=start_time, end_time=end_time, region=region
        )

        if spot_prices:
            # return the  most recent spot price
            return spot_prices[0]

        # api_url = "https://prices.azure.com/api/retail/prices"
        # query = f"contains(meterName, 'Spot') and skuName eq '{vm_type}'"
        # if region:
        #     query += f" and armRegionName eq '{region}'"
        # response = requests.get(api_url, params={'$filter': query})

        # if response.status_code == 200:
        #     data = response.json()
        #     items = data.get('Items', {})

        #     if items:
        #         for item in items:
        #             print(f"{item['productName']}: ${item['retailPrice']} per hour in location {item['location']}")
        #     else:
        #         print("No spot pricing data found for the specified instance.")
        # else:
        #     print("Failed to fetch pricing data:", response.status_code)
        #     print(response.text)

    def find_matching_vm_types(self, vcpus: int, memory: int):
        # List VM sizes in the specified region
        vm_sizes = self.compute_client.virtual_machine_sizes.list("eastus")

        # Filter for 16 vCPUs and 64 GB RAM
        matching_vms = [
            size.as_dict() for size in vm_sizes
            if size.number_of_cores == vcpus and size.memory_in_mb == memory * 1024
        ]

        return matching_vms

if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    container_name = os.getenv("azure_container_name")
    storage_name = os.getenv("azure_storage_name")
    if (
        subscription_id
        and resource_group_name
        and vm_name
        and container_name
        and storage_name
    ):
        azure = Azure_VM_Wrapper(subscription_id, resource_group_name)
        print(azure.find_matching_vm_types(vcpus=192, memory=2048))

        # end_time = datetime.now()
        # start_time = end_time - timedelta(days=30)
        # response = azure.get_spot_price_history(
        #     vm_type="Standard_M416s_6_v3",
        #     region="eastus",
        #     start_time=start_time,
        #     end_time=end_time,
        # )

        # print(response)
        
        # azure.get_azure_spot_prices("F16s Spot", "eastus2")
        # storage_wrapper = Storage_Wrapper(storage_name, subscription_id, resource_group_name)
        # blob_name = "hello_world.sh"
        # blob_url = storage_wrapper.get_blob_url(container_name, blob_name)
        # commands = [
        #     f"curl -o /home/azureuser/{blob_name} '{blob_url}'",
        #     f"chmod +x /home/azureuser/{blob_name}",
        #     f"/home/azureuser/{blob_name}"
        # ]
        # azure.execute_commands(vm_name, commands)
        # azure.stop_vm(vm_name)
