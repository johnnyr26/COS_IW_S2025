import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
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

    def get_last_id(self) -> int:
        return self.wiki_db.get_highest_id()

    def log_data(
        self,
        start_time: datetime,
        end_time: datetime,
        vm_name: str,
        num_uploads: int,
    ):
        prev_log = None
        log_id = self.log_db.get_highest_id()
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

        spot_price = self.ec2.get_spot_price(vm_name=vm_name)
        cost = Decimal(str(spot_price.price)) if spot_price else Decimal(0)

        new_log = Log(
            id=log_id + 1,
            start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            end_time=end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            virtual_machine=vm_name,
            num_uploads=num_uploads,
            total_uploads=int(prev_log['Item']['total_uploads']['N']) + num_uploads,
            cost=Decimal(cost),
            total_cost=Decimal(Decimal(prev_log['Item']['total_cost']['N']) + cost),
        )
        self.log_db.put_item(id=new_log.id, item=new_log.to_dict())

    def execute_task(self, id: int) -> bool:
        # uses a web scraper to scrape a Wikipedia article
        # and store its content to a database.
        try:
            # print("ID", id)
            response = self.web_scraper.scrape_wikipedia_article(
                url=f"https://en.wikipedia.org/?curid={id}"
            )
            # print("Web Scraper Response", response)
            self.wiki_db.put_item(id=id, item=response)
            return True
        except (WebsiteNotFoundException, ClientError):
            return True

    def run_simulation(
        self,
        aws_instance: str,
        azure_vm: str,
        start_time: datetime,
        end_time: datetime,
        prev_id: int = 0,
    ):
        started_vms = False
        prev_log_time: datetime | None = None
        curr_id = prev_id
        num_uploads = 0

        while datetime.now() > start_time and datetime.now() < end_time:
            if not started_vms:
                self.ec2.start_instance(instance_id=aws_instance)
                # self.azure.start_vm(vm_name=azure_vm)
                started_vms = True

            if prev_log_time == None:
                prev_log_time = datetime.now()

            # updates every 5 minutes, continues processing until termination.
            curr_time = datetime.now()
            if curr_time - timedelta(minutes=5) >= prev_log_time:
                self.log_data(
                    start_time=prev_log_time,
                    end_time=curr_time,
                    vm_name="AWS",
                    num_uploads=num_uploads,
                )
                prev_log_time = curr_time
                num_uploads = 0

            success = self.execute_task(id=curr_id)
            if success:
                num_uploads += 1
            curr_id += 1


if __name__ == "__main__":
    instance_id = os.getenv("aws_instance_id")
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    if subscription_id and resource_group_name and instance_id:

        ec2 = EC2_Wrapper()
        azure = Azure_VM_Wrapper(
            subscription_id=subscription_id, resource_group_name=resource_group_name
        )
        analyzer = Analyzer(ec2=ec2, azure=azure)
        id = analyzer.get_last_id()
        print("ID", id)
        analyzer.run_simulation(
            aws_instance=instance_id,
            azure_vm="Azure",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(minutes=5),
            prev_id=analyzer.get_last_id()
        )
