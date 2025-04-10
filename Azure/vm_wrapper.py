import os
import requests
from dotenv import load_dotenv
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import RunCommandInput, RunCommandResult
# from storage_wrapper import Storage_Wrapper

load_dotenv(override=True)

class Azure_VM_Wrapper():
    def __init__(
        self, 
        subscription_id: str, 
        resource_group_name: str
    ):
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
        start_vm_poller = self.compute_client.virtual_machines.begin_start(self.resource_group_name, vm_name)
        start_vm_poller.result()
        print(f"VM {vm_name} started")

    def stop_vm(self, vm_name: str):
        """
        Terminates a virtual machine.

        :param vm_name: the name of the virtual machine to terminate.
        """
        stop_vm_poller = self.compute_client.virtual_machines.begin_power_off(self.resource_group_name, vm_name)
        stop_vm_poller.result()
        print(f"VM {vm_name} terminated")

    def execute_commands(self, vm_name: str, commands: list[str]):
        """
        Executes a command on the virtual machine.

        :param vm_name: the name of the virtual machine to execute the command.
        :param commands: the list of commands to exceute on the virtual machine.
        """

        command_input = RunCommandInput(
            command_id='RunShellScript',
            script=commands
        )

        exec_command_poller = self.compute_client.virtual_machines.begin_run_command( # type: ignore
            resource_group_name=self.resource_group_name,
            vm_name=vm_name,
            parameters=command_input # type: ignore
        )

        result = exec_command_poller.result() # type: ignore

        if isinstance(result, RunCommandResult) and isinstance(result.value, list):
            for message in result.value:
                print(message.code)
                print(message.message)

    def get_azure_spot_price_history(
            self,
            vm_name: str,
            region: str
    ):
        """
        Fetches the spot price history for a particular Azure virtual machine.
        Uses the cloudprice API to fetch the prices from the past 30 days.

        :param vm_name: the VM name to fetch the price for.
        :param region: the region to fetch the VM spot price history for.
        """
        url = f"https://data.cloudprice.net/api/v1/price_history_vm"
        params = {
            "vmname": vm_name,
            "regions": region,
            "currency": "USD",
            "timerange": "last30Days",
            "tier": "spot",
            "payment": "payasyougo"
        }

        headers ={
            # Request headers
            'Cache-Control': 'no-cache',
            'subscription-key': os.getenv("cloudnet_subscription_primary_key", ""),
            'allowed-origins': '*',
        }

        spot_prices: list[dict[str, str | datetime]] = []

        response = requests.get(url=url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            history_price_values = data.get('listHistoryPriceValues', {})
            for data in history_price_values:
                spot_prices.append({
                    "instance": data.get('name'),
                    "price": data.get('linuxPrice'),
                    "timestamp": datetime.strptime(data.get('modifiedDate'), '%Y-%m-%d %H:%M:%S')
                })
            return spot_prices

    def get_azure_spot_prices(self, vm_type: str, region: str | None = None):
        """
        Fetches the current spot price for a particular Azure instance.

        :param vm_type: the VM instance type to fetch the price for.
        """
        api_url = "https://prices.azure.com/api/retail/prices"
        query = f"contains(meterName, 'Spot') and skuName eq '{vm_type}'"
        if region:
            query += f" and armRegionName eq '{region}'"
        response = requests.get(api_url, params={'$filter': query})

        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', {})

            if items:
                for item in items:
                    print(f"{item['productName']}: ${item['retailPrice']} per hour in location {item['location']}")
            else:
                print("No spot pricing data found for the specified instance.")
        else:
            print("Failed to fetch pricing data:", response.status_code)
            print(response.text)

            

if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    container_name = os.getenv("azure_container_name")
    storage_name = os.getenv("azure_storage_name")
    if subscription_id and resource_group_name and vm_name and container_name and storage_name:
        azure = Azure_VM_Wrapper(subscription_id, resource_group_name)
        response = azure.get_azure_spot_price_history(
            vm_name="Standard_M416s_6_v3",
            region="eastus"
        )
        print(response)
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