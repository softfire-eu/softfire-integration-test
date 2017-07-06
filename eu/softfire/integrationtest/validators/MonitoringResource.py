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
        
        cnt=1
        
        while 1:
            log.debug('Validate attempt: {}'.format(cnt))
            time.sleep(15)
            r = requests.get(res["url"])
            if r.status_code==200:
                if "zabbix.php" in r.text:
                    return
            cnt += 1
            if cnt >3:
                break
                
        raise MonitoringResourceValidationException(res)
