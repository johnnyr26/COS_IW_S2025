import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

load_dotenv(override=True)

class Blob_Wrapper():
    def __init__(self, storage_account_name: str):
        """
        Initializes the Azure VM Wrapper with the necessary credentials and subscriptions.
        Authenticates to the Azure account and creates a ComputeManageClient that provides
        low-level access to the virtual machines.

        :param subscription_id: the subscription id for the virtual machines.
        :param resource_group_name: the resource group name attached to the subscription.
        """
        try:
            account_url = f"https://{storage_account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(account_url, credential=credential)
        except Exception as ex:
            print("Failed to initialize Blob client", ex)


    def upload_file(self, filepath: str, container_name: str, blob: str):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob)
            print("Uploading to Azure Storage as blob:\n\t" + blob)
            with open(file=filepath, mode="rb") as data:
                blob_client.upload_blob(data)
                print(f"Blob upload {blob} succeeded.")
        except Exception as ex:
            print("Failed to upload blob", ex)

if __name__ == "__main__":
    storage_account_name = os.getenv("azure_storage_name")
    container_name = os.getenv("azure_container_name")
    if storage_account_name and container_name:
        blob = Blob_Wrapper(storage_account_name)
        blob.upload_file("Azure/hello_world.sh", container_name, "hello_world.sh")
