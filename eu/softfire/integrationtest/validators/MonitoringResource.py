import json
import logging
import subprocess
import time
import requests

from eu.softfire.integrationtest.main.experiment_manager_client import get_resource_from_id
from eu.softfire.integrationtest.utils.exceptions import MonitoringResourceValidationException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)



class MonitoringResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id):
        log.debug('Validate MonitoringResource with resource_id: {}'.format(resource_id))
        log.debug('Validate MonitoringResource with resource: {}'.format(resource))
        res = json.loads(resource)
        
        
        r = requests.get(res["url"])
        if r.status_code==200:
            return
        else:
            raise SecurityResourceValidationException(res)
