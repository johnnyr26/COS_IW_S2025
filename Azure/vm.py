import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient

load_dotenv()

class Azure():
    def __init__(
        self, 
        subscription_id: str, 
        resource_group_name: str
    ):
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        credential = DefaultAzureCredential()
        compute_client = ComputeManagementClient(credential, subscription_id)
        self.vms = compute_client.virtual_machines.list(resource_group_name)
        
    def describe_vms(self):
        for vm in self.vms:
            print(f"VM Name: {vm.name}")
            print(f"Resource Group: {resource_group_name}")
            print(f"Location: {vm.location}")
            if vm.storage_profile and vm.storage_profile.os_disk:
                print(f"Operating System: {vm.storage_profile.os_disk.os_type}")
            else:
                print("Operating System: Not available")



if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    if subscription_id and resource_group_name:
        azure = Azure(subscription_id, resource_group_name)
        azure.describe_vms()