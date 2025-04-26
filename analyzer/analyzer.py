import os
import ast
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from paramiko.ssh_exception import NoValidConnectionsError
from decimal import Decimal
from AWS.ec2_wrapper import EC2_Wrapper
from Azure.vm_wrapper import Azure_VM_Wrapper
from AWS.dynamo_db_wrapper import DynamoDB_Wrapper
from analyzer.web_scraper import Web_Scraper, WebsiteNotFoundException
from shared.log import Log

load_dotenv(override=True)


class Analyzer:
    def __init__(self, ec2: EC2_Wrapper, azure: Azure_VM_Wrapper):
        self.ec2 = ec2
        self.azure = azure
        self.wiki_db = DynamoDB_Wrapper(
            table_name="wikipedia_table", partition_key="id"
        )
        self.log_db = DynamoDB_Wrapper(table_name="log_table", partition_key="id")
        self.web_scraper = Web_Scraper()
        # start with ec2, switch over to azure
        self.vm: EC2_Wrapper | Azure_VM_Wrapper = ec2

    def get_last_id(self) -> int:
        return self.wiki_db.get_latest_id()

    def log_data(
        self,
        start_time: datetime,
        end_time: datetime,
        vm_name: str,
        num_uploads: int,
    ):
        prev_log = None
        log_id = self.log_db.get_latest_id()
        if log_id == 0:
            prev_log = Log(
                id=0,
                start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                end_time=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                virtual_machine=vm_name,
                num_uploads=0,
                total_uploads=0,
                cost=Decimal(0),
                total_cost=Decimal(0),
            )
        else:
            prev_log = self.log_db.get_item(key=str(log_id))

        if vm_name == "AWS":
            spot_price = self.ec2.get_spot_price(vm_name=vm_name)
        else:
            spot_price = self.azure.get_spot_price(vm_type=vm_name)

        cost = Decimal(str(spot_price.price)) if spot_price else Decimal(0)
        total_uploads = (
            num_uploads
            if log_id == 0
            else int(prev_log["Item"]["total_uploads"]["N"]) + num_uploads
        )
        total_cost = (
            cost
            if log_id == 0
            else (Decimal(Decimal(prev_log["Item"]["total_cost"]["N"]) + cost))
        )

        new_log = Log(
            id=log_id + 1,
            start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_time=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            virtual_machine=vm_name,
            num_uploads=num_uploads,
            total_uploads=total_uploads,
            cost=Decimal(cost),
            total_cost=total_cost,
        )
        self.log_db.put_item(id=new_log.id, item=new_log.to_dict())

    def execute_task(self, id: int, is_aws: bool) -> bool:
        # uses a web scraper to scrape a Wikipedia article
        # and store its content to a database.
        try:
            user = "ec2-user" if is_aws else "azureuser"

            response = self.vm.execute_commands(
                commands=[f"python3 /home/{user}/web_scraper.py {id}"]
            )
            print("RESPONSE", response)
            if response:
                response = ast.literal_eval(response)
                self.wiki_db.put_item(id=id, item=response)
            return True
        except (WebsiteNotFoundException, ClientError):
            return False
        except (NoValidConnectionsError, Exception):
            time.sleep(5)
            return False

    def run_simulation(
        self,
        aws_instance: str,
        azure_vm: str,
        start_time: datetime,
        end_time: datetime,
        prev_id: int = 0,
    ):
        prev_log_time: datetime | None = None
        curr_id = prev_id
        num_uploads = 0
        is_aws = True

        while datetime.now() > start_time and datetime.now() < end_time:
            if prev_log_time == None:
                prev_log_time = datetime.now()

            # updates every 5 minutes, continues processing until termination.
            curr_time = datetime.now()
            if curr_time - timedelta(minutes=1) >= prev_log_time:
                self.log_data(
                    start_time=prev_log_time,
                    end_time=curr_time,
                    vm_name="AWS" if is_aws else "Azure",
                    num_uploads=num_uploads,
                )
                prev_log_time = curr_time
                num_uploads = 0
                is_aws = not is_aws
            if is_aws and self.ec2.get_instance_state(instance_id=aws_instance) != "running":
                self.ec2.start_instance(instance_id=aws_instance)
                self.azure.stop_vm(vm_name=azure_vm)
            if not is_aws and self.azure.get_vm_state(vm_name=azure_vm) != "VM running":
                self.azure.start_vm(vm_name=azure_vm)
                self.ec2.stop_instance(instance_id=aws_instance)

            if is_aws and self.ec2.get_instance_state(instance_id=aws_instance) == "running":
                self.vm = self.ec2
            if not is_aws and self.azure.get_vm_state(vm_name=azure_vm) == "VM running":
                self.vm = self.azure

            success = self.execute_task(id=curr_id, is_aws=is_aws)
            if success:
                num_uploads += 1
            curr_id += 1


if __name__ == "__main__":
    instance_id = os.getenv("aws_instance_id")
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    azure_vm_name = os.getenv("azure_vm_name")
    if subscription_id and resource_group_name and instance_id and azure_vm_name:
        ec2 = EC2_Wrapper()
        azure = Azure_VM_Wrapper(
            subscription_id=subscription_id, resource_group_name=resource_group_name
        )
        analyzer = Analyzer(ec2=ec2, azure=azure)
        id = analyzer.get_last_id()
        analyzer.run_simulation(
            aws_instance=instance_id,
            azure_vm=azure_vm_name,
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=5),
            prev_id=analyzer.get_last_id(),
        )
