from airflow import DAG
from airflow.operators.python import PythonOperator
from azure.mgmt.resource.resources.models import ResourceGroupExportResult
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential
import os

def create_container(blobClient: BlobServiceClient, subscription_id:str, subscription_name: str) -> ContainerClient:
    try:
        cc =  blobClient.create_container(subscription_id)
        cc.set_container_metadata({
            'subscription_name': subscription_name
        })
        return cc
    except Exception as e:
        cc = blobClient.get_container_client(subscription_id)
        return cc
    
def save_as_blob(content: str, subId: str, subName: str, resourceGroup: str):
    cred = DefaultAzureCredential()
    storage_name = os.environ.get('AIRFLOW_ARM_EXPORT_STORAGE_NAME')
    storage_url = os.environ.get('AIRFLOW_ARM_EXPORT_STORAGE_URL')

    blobClient = BlobServiceClient(storage_url, credential=cred)

    # subscription name as container
    container = create_container(blobClient, subId, subName)

    container.upload_blob(resourceGroup, data=content, overwrite=True)
    
    
def export_arm_to_azblob(**kwargs):
    pass


def create_operator_export_arm(index: int, subId: str, subName: str, resourceGroup: str, dag: DAG):
    operator = PythonOperator(
            task_id = f'export_arm_{subName}_{resourceGroup}',
            python_callable = export_arm_to_azblob,
            dag=dag,
            op_kwargs={
                'subscription_id': subId,
                'subscription_name': subName,
                'resource_group': resourceGroup
            }
    )
    return operator