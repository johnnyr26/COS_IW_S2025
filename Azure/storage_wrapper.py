import os
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from azure.mgmt.storage import StorageManagementClient

load_dotenv(override=True)

class Storage_Wrapper():
    def __init__(
            self, 
            storage_account_name: str, 
            subscription_id: str,
            resource_group_name: str,
        ):
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
            self.storage_client = StorageManagementClient(credential, subscription_id=subscription_id)
            self.storage_account_name = storage_account_name
            self.resource_group_name = resource_group_name
        except Exception as ex:
            print("Failed to initialize Blob client", ex)


    def upload_file(self, filepath: str, container_name: str, blob_name: str):
        """
        Uploads a file as a blob to Azure Blob

        :param filepath: the local path of the file to be uploaded.
        :param container_name: the name of the container to upload the file to.
        :param blob: the name of the blob (file) that will appear when uploaded to the container.
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            print("Uploading to Azure Storage as blob:\n\t" + blob_name)
            with open(file=filepath, mode="rb") as data:
                blob_client.upload_blob(data)
                print(f"Blob upload {blob_name} succeeded.")
        except Exception as ex:
            print("Failed to upload blob", ex)

    def get_blob_url(self, container_name: str, blob_name: str) -> str | None:
        """
        Gets the blob url for the particular blob on the container.
        First retrieves the account key (refreshes periodically),
        and then generates the blob sas (shared access signature)
        to produce the url for retrieving the blob.

        :param container_name: the name of the container that holds the blob.
        :param blob: the name of the blob that is stored in the container.
        """
        account_key = self._get_account_key()
        if account_key:
            sas_token = generate_blob_sas(
                account_name=self.storage_account_name,
                container_name=container_name,
                blob_name=blob_name,
                account_key=account_key,
                permission=BlobSasPermissions(read=True),
                expiry=(datetime.now(timezone.utc) + timedelta(hours=1))
            )

            sas_url = f"https://{self.storage_account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
            return sas_url
        return None
    
    def delete_blob(self, container_name: str, blob_name: str):
        """
        Deletes a blob from the storage account.

        :param container_name: the name of the container to upload the file to.
        :param blob: the name of the blob (file) to be deleted.
        """
        print(f"Deleting blob {blob_name} in container {container_name}...")
        blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=blob_name)
        blob_client.delete_blob(delete_snapshots="include")
        print(f"Blob {blob_name} in container {container_name} has been deleted successfully")
    
    def _get_account_key(self) -> str | None:
        """
        Gets the first account key for the storage account.
        Two account keys for the storage account exists.
        This method retrieves the first account key.
        """
        keys = self.storage_client.storage_accounts.list_keys(self.resource_group_name, self.storage_account_name)
        if keys.keys:
            return keys.keys[0].value
        return None
    
    
        


if __name__ == "__main__":
    storage_account_name = os.getenv("azure_storage_name")
    container_name = os.getenv("azure_container_name")
    subscription_id = os.getenv("azure_subscription_id")
    resource_group_name = os.getenv("azure_resource_group_name")
    if storage_account_name and container_name and subscription_id and resource_group_name:
        blob_name = "hello_world.sh"
        storage = Storage_Wrapper(storage_account_name, subscription_id, resource_group_name)
        storage.delete_blob(container_name=container_name, blob_name=blob_name)
        storage.upload_file(filepath="Azure/hello_world.sh", container_name=container_name, blob_name=blob_name)



