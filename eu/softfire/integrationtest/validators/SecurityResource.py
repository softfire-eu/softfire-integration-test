import json
import logging
import time

import requests

from eu.softfire.integrationtest.main.experiment_manager_client import get_resource_from_id
from eu.softfire.integrationtest.utils.exceptions import SecurityResourceValidationException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)

wait_nfv_resource_minutes = int(get_config_value('nfv-resource', 'wait-nfv-res-min', '7'))


class SecurityResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id):
        log.debug('Validate SecurityResource with resource_id: {}'.format(resource_id))
        res = json.loads(resource)
        for i in range(wait_nfv_resource_minutes * 20):
            for k, v in res.items():
                if "ERROR" in v.upper():
                    raise SecurityResourceValidationException(v)
                elif "link" in k:
                    resp = requests.get(v)
                    if resp.status_code != 200:
                        raise SecurityResourceValidationException(v)
                elif (k == "status" and v == "NULL") or (k == "NSR Details"):
                    res = json.loads(get_resource_from_id(resource_id))
                    time.sleep(3)
                else:
                    return
        return
