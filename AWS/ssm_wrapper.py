import os
import time
from dotenv import load_dotenv
import boto3
from mypy_boto3_ssm.client import SSMClient


load_dotenv(override=True)


class SSM_Wrapper():
    def __init__(self, ssm: SSMClient):
        self.ssm = ssm

    def execute_commands(self, instance_id: str, commands: list[str]):
        response = self.ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': commands}
        )

        if "Command" in response and "CommandId" in response["Command"]:
            command_id = response["Command"]["CommandId"]
            print("SSM command sent. Command ID:", command_id)

            while True:
                time.sleep(5)  

                output = self.ssm.get_command_invocation(
                    CommandId=command_id,
                    InstanceId=instance_id
                )

                if output['Status'] in ['Success', 'Failed']:
                    print("STDOUT:\n", output.get("StandardOutputContent"))
                    print("STDERR:\n", output.get("StandardErrorContent"))
                    break

                          

                
if __name__ == "__main__":
    ssm = SSM_Wrapper(boto3.client('ssm'))
    instance_id = os.getenv('aws_instance_id') 
    if  instance_id:
        command = f"/home/ec2-user/hello_world.sh"
        ssm.execute_commands(instance_id, [command])