from airflow import DAG
from airflow.operators.python import PythonOperator
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import logging
    

def export_arm_template(**kwargs):
    pass

def create_operator_export_arm(subId: str, subName: str, resourceGroup: str, storageUrl:str, dag: DAG):
    '''
        creates python operator
    '''

    cred = DefaultAzureCredential()

    operator = PythonOperator(
            task_id = f'export_arm_{subName}_{resourceGroup}',
            python_callable = export_arm_template,
            dag=dag,
            op_kwargs={
                'subscriptionId': subId,
                'subscriptionName': subName,
                'resource_group': resourceGroup,
                'azureCred': cred,
                'storageUrl': storageUrl
            }
    )
    
    return operator