from azure.identity import DefaultAzureCredential
from  azure.mgmt.resource.resources.v2019_07_01 import *
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.resource.resources.models import ResourceGroupExportResult
from azure.storage.blob import BlobServiceClient, ContainerClient
import json 

# arm template schema
# https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/syntax

# resource management client
# https://learn.microsoft.com/en-us/python/api/azure-mgmt-resource/azure.mgmt.resource.resources.v2022_09_01.operations.resourcegroupsoperations?view=azure-python#azure-mgmt-resource-resources-v2022-09-01-operations-resourcegroupsoperations-begin-export-template

#storage client
# https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python?tabs=managed-identity%2Croles-azure-portal%2Csign-in-azure-cli&pivots=blob-storage-quickstart-scratch


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

storage_name = 'strgarmtemplates'
storage_url = f'https://{storage_name}.blob.core.windows.net/'
cred = DefaultAzureCredential()
blobClient = BlobServiceClient(storage_url, credential=cred)

def export_template_and_upload_as_blob(resourceList: list[str], resource_group_name: str, blob_name: str):
    # export template has a limit of 200 resources per resource group
    result: ResourceGroupExportResult = rmc.resource_groups.begin_export_template(resource_group_name, {
    'resources': resourceList ,#['*'],
    'options': 'SkipResourceNameParameterization,SkipAllParameterization'
    })

    result.wait()

    templateDict = result.result().template

    jsonStr = json.dumps(templateDict, indent=4)

    # subscription name as container
    container = create_container(blobClient, sub.subscription_id, sub.display_name)

    container.upload_blob(blob_name, data=jsonStr, overwrite=True)


sc =SubscriptionClient(credential=cred)
subscriptions = sc.subscriptions.list()

for sub in subscriptions:

    rmc = ResourceManagementClient(credential=cred, subscription_id=sub.subscription_id)

    for rg in rmc.resource_groups.list():
        
        resources= []
        resources_bucket_of_200 = []
        rscByRG = rmc.resources.list_by_resource_group(rg.name)

        for rsc in rscByRG:
        
            if len(resources_bucket_of_200) > 200:
                resources.append(resources_bucket_of_200.copy())
                resources_bucket_of_200 = [rsc.id]
            else:
                resources_bucket_of_200.append(rsc.id)
        else:
            # < 200 resources
            if not resources:
                resources.append(resources_bucket_of_200.copy())
            # > 200 resources, add remainder resources
            elif resources and len(resources_bucket_of_200) >= 1:
                resources.append(resources_bucket_of_200.copy())


        # within 200 resource range
        if len(resources) == 1 and resources[0]:
            export_template_and_upload_as_blob(resources[0], rg.name, f'{rg.name}.json')
            continue


        bucket_count = 1
        for bucket in resources:
            
            if not bucket:  # check resource group is empty
                continue
            
            export_template_and_upload_as_blob(bucket, rg.name, f'{rg.name}_{bucket_count}.json')
        
            bucket_count += 1

print('export template completed')

        


        
        


