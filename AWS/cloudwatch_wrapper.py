import os
from dotenv import load_dotenv
import boto3
from mypy_boto3_cloudwatch import CloudWatchClient
from datetime import datetime, timedelta


load_dotenv(override=True)

class Cloudwatch_Wrapper():
    def __init__(self, cloudwatch: CloudWatchClient):
        """
        Initializes the Cloudwatch wrapper.

        :param ce: A Boto3 Cloudwatch client. This client provides low-level
                    access to AWS Cloudwatch services.
        """
        self.cloudwatch = cloudwatch

    def get_metrics(
        self,
        instance_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, datetime | float | None]]:
        """
        Fetches the cost and hourly usage of the EC2 instance.
        Granularity is set daily.

        :param start_time: string format of the start date.
        :param end_time: string format of the end date.

        :return: A dictionary with the time period and CPU usage for each hour in the given time period.
        """
        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600, 
            Statistics=['Average'],
            Unit='Percent'
        )

        metrics_data: list[dict[str, datetime | float | None]] = [
            {
                "Time": res.get('Timestamp', None), 
                "CPU": res.get("Average", None)
            }
            for res in response.get("Datapoints", [])
        ]

        return metrics_data
    
if __name__ == "__main__":
    cloudwatch = Cloudwatch_Wrapper(boto3.client("cloudwatch"))
    instance_id = os.getenv("aws_instance_id")

    if instance_id:
        end_time = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        start_time = end_time - timedelta(weeks=1)
        response = cloudwatch.get_metrics(
            start_time=start_time,
            end_time=end_time,
            instance_id=instance_id
        )
        print(response)


