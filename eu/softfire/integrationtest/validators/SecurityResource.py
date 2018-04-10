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
    def validate(self, resource, resource_id, session):
        log.debug('Validate SecurityResource with resource_id: {}'.format(resource_id))
        for i in range(wait_nfv_resource_minutes * 20):
            res = json.loads(get_resource_from_id(resource_id, session))
            for k, v in res.items():
                if "ERROR" in str(v).upper():
                    raise SecurityResourceValidationException(v)
            if res.get('status') == 'ACTIVE':
                if res.get('resource_id') != 'firewall':
                    log.debug('Not a firewall SecurityResource')
                    return
                api_url = res.get('api_url')
                resp = requests.get(api_url + '/ufw/status')
                if resp.status_code != 200:
                    raise SecurityResourceValidationException(resp.text)
                else:
                    log.debug('SecurityResource with resource_id firewall is valid')
                    return
            time.sleep(3)
        else:
            raise SecurityResourceValidationException('Security resource did not reach active state.')
