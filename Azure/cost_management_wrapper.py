import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, UTC, date
from azure.identity import DefaultAzureCredential
from azure.mgmt.costmanagement import CostManagementClient
from datetime import datetime, timedelta

load_dotenv(override=True)


class Cost_Management_Wrapper:
    def __init__(self, subscription_id: str, resource_group_name: str):
        """
        Initializes the Azure Cost Management Wrapper with the subscription ID
        and the resouce group name. Authenticates the CostManagementClient.
        Provides low-level access to the Azure Cost Management Resources.

        :param subscription_id: the subscription id for the virtual machines.
        :param resource_group_name: the resource group name attached to the subscription.
        """
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        credential = DefaultAzureCredential()
        self.cost_management_client = CostManagementClient(credential)

    def get_cost(self, start_time: datetime, end_time: datetime, vm_name: str):
        """
        Gets the daily financial cost of the VM instance usage.

        :params start_time: the start time for measuring the VM cost.
        :params end_time: the end time for measuring the VM cost.
        :params vm_name: the name of the virtual machine to measure cost.
        :returns: list of time period and their cost.
        """
        query = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "time_period": {
                "from": start_time.isoformat(),
                "to": end_time.isoformat(),
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            },
        }

        resource_id = ("subscriptions/{}/" "resourceGroups/{}/").format(
            self.subscription_id, self.resource_group_name
        )

        print("Resource ID", resource_id)

        cost: list[dict[str, float | dict[str, str]]] = []
        response = self.cost_management_client.query.usage(
            scope=resource_id, parameters=query
        )
        for row in response.rows:
            print(row)
            cost.append({"time_period": row[0], "cost": row[1]})

        return cost


if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    if subscription_id and resource_group_name and vm_name:
        cost = Cost_Management_Wrapper(
            subscription_id=subscription_id, resource_group_name=resource_group_name
        )
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=30)

        response = cost.get_cost_and_usage(
            start_time=start_time, end_time=end_time, vm_name=vm_name
        )
        print(response)
