from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient
import json
import logging
import time, datetime


class ExportARMResult:
    def __init__(self, subscriptionId: str) -> None:
        self.armTemplateFileNames = []
        self.subscriptionId = ''
        self.exportSuccessful = True


class ExportARMHelper:

    def __init__(self,  azureCred: DefaultAzureCredential, subscriptionId, subscriptionName, resourceGroup, storageUrl) -> None:
        self.logger = logging.getLogger(__name__)
        self.rmc = ResourceManagementClient(credential=azureCred, subscription_id=subscriptionId)
        self.blobClient = BlobServiceClient(storageUrl, credential=azureCred)
        self.subscriptionId = subscriptionId
        self.subscriptionName = subscriptionName
        self.resourceGroup = resourceGroup
        self.exportResult = ExportARMResult(self.subscriptionId)


    def now_time_str(self):
        return datetime.datetime.now().strftime("%d_%m_%Y_%H_%M_%S")

    def create_blob_container_if_not_exist(self) -> ContainerClient:
        try:
            cc =  self.blobClient.create_container(self.subscriptionId)
            cc.set_container_metadata({
                'subscription_name': self.subscriptionName
            })
            return cc
        except Exception as e:
            cc = self.blobClient.get_container_client(self.subscriptionId)
            return cc
    

    def save_as_blob(self, content: str) -> str:
        '''
            subscription id is container name.
            Not using subscription name as container name due to naming convention is not 
        '''

        # subscription name as container
        container = self.create_blob_container_if_not_exist()

        blobName = f'{self.resourceGroup}_{self.now_time_str()}.json'

        container.upload_blob(blobName, data=content, overwrite=True)

        return blobName


    def export_arm_as_json_str(self, resourceIds: list[str]) -> str:
        result = self.rmc.resource_groups.begin_export_template(self.resourceGroup, {
        'resources': resourceIds,
        'options': 'SkipResourceNameParameterization,SkipAllParameterization'
        })

        result.wait()

        templateDict = result.result().template

        jsonStr = json.dumps(templateDict, indent=4)

        return jsonStr
        

    def export_arm_to_azblob(self):
        """
            **kwargs contains subscription name, subscription id, resource group and DefaultAzureCredential object
        """

        try:

            resources= []
            #resources_bucket_of_200 = []
            rscByRG = self.rmc.resources.list_by_resource_group(self.resourceGroup)


            while rscByRG:
                
                next = None
                
                if len(resources) < 200:

                    try:
                        next = rscByRG.next()
                    except:
                        break

                    resources.append(next.id)
                    continue

                armJson = self.export_arm_as_json_str(resources)
                blobName = self.save_as_blob(armJson)
                self.exportResult.armTemplateFileNames.append(blobName)
                resources = []

            # iterable does not have len(), hence,
            # resources will not be empty if resources < 200
            # or resource more than 200 but less than 400
            if resources:
                blobName = self.save_as_blob(armJson)
                self.exportResult.armTemplateFileNames.append(blobName)
                self.save_as_blob(armJson)
                
            return self.result

        except Exception as e:
            self.logger.error(str(e))
            self.exportResult.exportSuccessful = False
            return self.exportResult
