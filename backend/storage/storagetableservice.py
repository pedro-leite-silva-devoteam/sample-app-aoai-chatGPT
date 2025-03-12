import os
import asyncio
from azure.data.tables import TableServiceClient
from azure.core.exceptions import AzureError

class StorageTablesClient:
    def __init__(self):
        try:
            self.access_key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
            self.endpoint_suffix = os.environ["AZURE_STORAGE_ENDPOINT_SUFFIX"]
            self.account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
            self.container = os.environ["AZURE_STORAGE_CONTAINER"]
            self.folder = os.environ["AZURE_STORAGE_FOLDER"]
            self.blobs_table = os.environ["AZURE_STORAGE_BLOBS_TABLE"]
            self.tags_table = os.environ["AZURE_STORAGE_TAGS_TABLE"]
            self.blob_tags_table = os.environ["AZURE_STORAGE_BLOB_TAGS_TABLE"]

            self.connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={self.account_name};"
                f"AccountKey={self.access_key};"
                f"EndpointSuffix={self.endpoint_suffix}"
            )

            self.table_service_client = TableServiceClient.from_connection_string(self.connection_string)

        except AzureError as e:
            raise ValueError("Unable to connect to the Azure Storage Account") from e
        except Exception as e:
            raise RuntimeError("Unknown error occurred during connection initialization") from e

    def get_blob_url(self, file_name: str) -> str:
        if not self.account_name or not self.container or not self.folder:
            raise ValueError("Storage account name, container, or folder is missing in environment variables")

        return f"https://{self.account_name}.blob.{self.endpoint_suffix}/{self.container}/{self.folder}/{file_name}"

    async def query_by_blob_file_name(self, file_name: str):
        try:
            table_client = self.table_service_client.get_table_client(self.blobs_table)
            blob_url = self.get_blob_url(file_name)

            entities = await asyncio.to_thread(
                table_client.query_entities,
                f"BlobURL eq '{blob_url}'"
            )

            result = [entity for entity in entities]

            if len(result) > 1:
                raise ValueError(f"Multiple entities found with BlobURL: {blob_url}")

            return result

        except AzureError as e:
            raise ValueError(f"Error occurred while querying the Azure Table: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Exception in query_by_blob_file_name: {e}") from e

    async def query_by_blob_file_names(self, file_names: list):
        results = {}
        
        for file_name in file_names:
            try:
                table_client = self.table_service_client.get_table_client(self.blobs_table)
                blob_url = self.get_blob_url(file_name)

                entities = await asyncio.to_thread(
                    table_client.query_entities,
                    f"BlobURL eq '{blob_url}'"
                )

                result = [entity for entity in entities]

                if len(result) == 1:
                    uri = result[0].get('SourceURI', None)
                else:
                    uri = None

                results[file_name] = uri

            except AzureError as e:
                results[file_name] = None
                continue
            except Exception as e:
                results[file_name] = None
                continue

        return results
