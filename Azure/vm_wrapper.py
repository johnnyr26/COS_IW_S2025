import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.compute.models import RunCommandInput, RunCommandResult

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


if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    if subscription_id and resource_group_name and vm_name:
        azure = Azure_VM_Wrapper(subscription_id, resource_group_name)
        # azure.describe_vms()

        # Commands to run
        commands = [
            "echo Hello from VM",
            "echo This is an error >&2"
        ]
        # azure.start_vm(vm_name)
        azure.execute_commands(vm_name, commands)
        # azure.stop_vm(vm_name)