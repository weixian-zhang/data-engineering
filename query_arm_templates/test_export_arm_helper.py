import pytest
import os
from azure.identity import DefaultAzureCredential
from export_arm_helper import ExportARMHelper, ExportARMResult

subscriptionId = os.environ.get('AZURE_SUBSCRIPTION_ID')
subscriptionName = os.environ.get('AZURE_SUBSCRIPTION_NAME')
azureCred = DefaultAzureCredential()
storageUrl = os.environ.get('AIRFLOW_ARM_EXPORT_STORAGE_URL')
rgLessThan200 = 'gcc-hk' #'rg-azworkbench-dev'
rgMoreThan200 = 'rgGCCSHOL'

# *** this is an integration test to make up for lost of local debug capability when developing airflow on Windows
    
def test_export_arm_helper_less_than_200_resources_per_rg():
    helper = ExportARMHelper(azureCred, subscriptionId, subscriptionName, rgLessThan200, storageUrl)
    success = helper.export_arm_to_azblob()
    assert success == True


def test_export_arm_helper_more_than_200_resources_per_rg():
    helper = ExportARMHelper(azureCred, subscriptionId, subscriptionName, rgMoreThan200, storageUrl)
    result = helper.export_arm_to_azblob()
    assert result
    

# test_export_arm_helper_less_than_200_resources_per_rg()

test_export_arm_helper_more_than_200_resources_per_rg()