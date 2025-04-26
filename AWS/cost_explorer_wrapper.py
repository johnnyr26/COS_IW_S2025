import boto3
from datetime import datetime, timedelta


class Cost_Explorer_Wrapper:
    def __init__(self):
        """
        Initializes the CostExplorer wrapper.

        :param ce: A Boto3 CE client. This client provides low-level
                    access to AWS CE services.
        """
        self.ce = boto3.client("ce")

    def get_cost(
        self,
        instance_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """
        Fetches the cost and hourly usage of the EC2 instance.
        Granularity is set daily.

        :param start_time: string format of the start date.
        :param end_time: string format of the end date.

        :return: A dictionary with the total cost, total hourly usage, and cost/usasge by day
        """
        response = self.ce.get_cost_and_usage(
            TimePeriod={
                "Start": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "End": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            Granularity="HOURLY",
            Metrics=["UnblendedCost"],
            Filter={
                "Tags": {"Key": "NAME", "Values": [instance_name]},
            },
            GroupBy=[{"Type": "DIMENSION", "Key": "USAGE_TYPE"}],
        )

        print(response)

        total_cost = 0

        for group in response["ResultsByTime"][0]["Groups"]:
            usage_type = group["Keys"][0]
            cost = group["Metrics"]["UnblendedCost"]["Amount"]
            total_cost += float(cost)

        return total_cost


if __name__ == "__main__":
    ce = Cost_Explorer_Wrapper()
    print(
        ce.get_cost(
            start_time=datetime.now() - timedelta(days=30),
            end_time=datetime.now(),
            instance_name="COS IW Free Tier",
        )
    )
