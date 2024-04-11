from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime
from azure.identity import DefaultAzureCredential, UsernamePasswordCredential, InteractiveBrowserCredential
from  azure.mgmt.resource.resources.v2019_07_01 import *
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
import os
from operator_export_arm_to_blob import create_operator_export_arm

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'start_date': datetime(2024, 4,9)
}

def create_azure_cred():
    # production usage
    return DefaultAzureCredential()

    # devtest usage to get multiple subscirptions
    # testTenantId = os.environ.get('AIRFLOW_TEST_MS_TENANT_TENANTID')
    # testUsername = os.environ.get('AIRFLOW_TEST_MS_TENANT_USER_NAME')
    # testPassword = os.environ.get('AIRFLOW_TEST_MS_TENANT_USER_PASSWORD')
    # clientId = '04b07795-8ddb-461a-bbee-02f9e1bf7b46' #client id of azcli # os.environ.get('AIRFLOW_TEST_MS_TENANT_CLIENTID')
    # return UsernamePasswordCredential(username=testUsername, password=testPassword, client_id=clientId, tenant_id = testTenantId)
    #return InteractiveBrowserCredential(tenant_id=testTenantId)



def get_subs_and_rgs():

    result = []

    cred = create_azure_cred()

    sc = SubscriptionClient(credential=cred)

    subscriptions = sc.subscriptions.list()

    for sub in subscriptions:

        rmc = ResourceManagementClient(credential=cred, subscription_id=sub.subscription_id)

        for rg in rmc.resource_groups.list():
            result.append(
                {
                    'subscription_id': sub.id,
                    'subscription_name': sub.display_name,
                    'resource_group': rg.name
                }
            )

    return result


with DAG(
            dag_id='arm_export_dag',
            default_args=default_args,
            catchup=False,
            schedule_interval='@once' # or None
            
         ) as dag:
    
    start = EmptyOperator(task_id='start')
    
    subRGs = get_subs_and_rgs()

    for idx, srg in enumerate(subRGs):
        subId = srg['subscription_id']
        subName = srg['subscription_name']
        rg = srg['resource_group']

        export_arm_operator = create_operator_export_arm(index=idx, subId=subId, subName=subName, resourceGroup=rg, dag=dag)

        start >> export_arm_operator