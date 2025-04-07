import os
import datetime
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient

load_dotenv(override=True)

class Monitor_Wrapper():
    def __init__(
        self,
        subscription_id: str, 
        resource_group_name: str
    ):
        """
        Initializes the Azure Monitor Wrapper with the subscription ID
        and the resouce group name. Authenticates the MonitorManagementClient.
        Provides low-level access to the Azure Monitor Resources.

        :param subscription_id: the subscription id for the virtual machines.
        :param resource_group_name: the resource group name attached to the subscription.
        """
        self.subscription_id = subscription_id
        self.resource_group_name = resource_group_name
        credential = DefaultAzureCredential()
        self.monitor_client = MonitorManagementClient(
            credential,
            subscription_id
        )


    def get_metrics(
            self, 
            vm_name: str, 
            start_time: datetime, 
            end_time: datetime
        ) -> list[dict[str, datetime | float]]:
        """
        Gets the CPU percentage usage for the virtual machine in the given period.

        :param vm_name: the name of the virtual machine to analyze CPU usage.
        :param start_time: the start time for the metric analysis.
        :param end_time: the end time for the metric analysis.
        :return:  A dictionary with the time period and CPU usage for each hour in the given time period.
        """
        resource_id = (
            "subscriptions/{}/"
            "resourceGroups/{}/"
            "providers/Microsoft.Compute/virtualMachines/{}"
        ).format(self.subscription_id, self.resource_group_name, vm_name)

        response_data = self.monitor_client.metrics.list(
            resource_id,
            timespan="{}/{}".format(start_time, end_time),
            interval=timedelta(hours=1),
            metricnames='Percentage CPU',
            aggregation='Average'
        )

        metrics_data: list[dict[str, datetime | float]] = []
        
        for item in response_data.value:
            # print("{} ({})".format(item.name.localized_value, item.unit))
            for timeserie in item.timeseries:
                for data in timeserie.data:
                    metrics_data.append({
                        "Time": data.time_stamp,
                        "CPU": data.average,
                    })
                    # print("{}: {}".format(data.time_stamp, data.average))

        return metrics_data

    
if __name__ == "__main__":
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    vm_name = os.getenv("azure_vm_name")
    if subscription_id and resource_group_name and vm_name:
        monitor = Monitor_Wrapper(
            subscription_id=subscription_id, 
            resource_group_name=resource_group_name
        )
        end_time = datetime.now(UTC).replace(tzinfo=None)
        start_time = end_time - timedelta(days=3)
        response = monitor.get_metrics(vm_name=vm_name, start_time=start_time, end_time=end_time)
        print(response)
 