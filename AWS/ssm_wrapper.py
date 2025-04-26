import os
import time
from dotenv import load_dotenv
import boto3
from mypy_boto3_ssm.client import SSMClient


load_dotenv(override=True)


class SSM_Wrapper:
    def __init__(self):
        """
        Initializes the SSM client.

        :param ssm: A Boto3 SSM client. This client allows user to execute
                        commands on EC2 instances.
        """
        self.ssm = boto3.client('ssm')

    def execute_commands(self, instance_id: str, commands: list[str]):
        """
        Executes a series of commands on the ec2 instance. Prints out
        the standard output and standard error.

        :param instance_id: The instance id of the EC2 instance to start.
        :param commands: The list of commands to execute sequentially on the EC2 instance.
        """
        print("EXECUTING COMMAND")
        response = self.ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={"commands": commands},
        )

        if "Command" in response and "CommandId" in response["Command"]:
            command_id = response["Command"]["CommandId"]
            print("SSM command sent. Command ID:", command_id)

            while True:
                time.sleep(3)

                output = self.ssm.get_command_invocation(
                    CommandId=command_id, InstanceId=instance_id
                )

                if output["Status"] in ["Success", "Failed"]:
                    return output.get("StandardOutputContent")


if __name__ == "__main__":
    ssm = SSM_Wrapper()
    instance_id = os.getenv("aws_instance_id")
    if instance_id:
        command = f"python3 /home/ec2-user/web_scraper.py 10"
        print(ssm.execute_commands(instance_id, [command]))
