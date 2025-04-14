import boto3
from mypy_boto3_ce import CostExplorerClient


class Cost_Explorer_Wrapper:
    def __init__(self, ce: CostExplorerClient):
        """
        Initializes the CostExplorer wrapper.

        :param ce: A Boto3 CE client. This client provides low-level
                    access to AWS CE services.
        """
        self.ce = ce

    def get_cost_and_usage(
        self,
        start_date: str,
        end_date: str,
    ) -> dict[str, list[dict[str, float | dict[str, str]]] | float]:
        """
        Fetches the cost and hourly usage of the EC2 instance.
        Granularity is set daily.

        :param start_time: string format of the start date.
        :param end_time: string format of the end date.

        :return: A dictionary with the total cost, total hourly usage, and cost/usasge by day
        """
        response = self.ce.get_cost_and_usage(
            TimePeriod={"Start": start_date, "End": end_date},
            Granularity="DAILY",
            Metrics=["UnblendedCost", "UsageQuantity"],
        )
        cost: list[dict[str, float | dict[str, str]]] = []
        usage_quantity: list[dict[str, float | dict[str, str]]] = []

        total_cost = 0
        total_hours = 0
        for data in response["ResultsByTime"]:
            total_data = data.get("Total", {})
            unblended_cost = total_data.get("UnblendedCost", {}).get("Amount")
            if unblended_cost is not None:
                total_cost += float(unblended_cost)
                cost.append(
                    {
                        "time_period": {
                            k: str(v) for k, v in data.get("TimePeriod", {}).items()
                        },
                        "cost": float(unblended_cost),
                    }
                )

            usage_quantity_data = total_data.get("UsageQuantity", {}).get("Amount")
            if usage_quantity_data is not None:
                total_hours += float(usage_quantity_data)
                usage_quantity.append(
                    {
                        "time_period": {
                            k: str(v) for k, v in data.get("TimePeriod", {}).items()
                        },
                        "usage": float(usage_quantity_data),
                    }
                )

        return {
            "cost_by_day": cost,
            "hours_by_day": usage_quantity,
            "total_cost": total_cost,
            "total_hours": total_hours,
        }


if __name__ == "__main__":
    ce = Cost_Explorer_Wrapper(boto3.client("ce"))
    print(ce.get_cost_and_usage(start_date="2025-04-01", end_date="2025-04-07"))
