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
        nsr = None
        for i in range(wait_nfv_resource_minutes * 20):
            time.sleep(3)
            resource = get_resource_from_id(resource_id, session)
            try:
                nsr = json.loads(resource)
            except Exception as e:
                log.error('Not able to parse resource: {}'.format(resource))
                raise SecurityResourceValidationException('Not able to parse resource: {}'.format(resource))
#            res = json.loads(get_resource_from_id(resource_id, session))
            nsr_status = nsr.get('status')
            log.debug("Status of nsr is %s" % nsr_status)
            if not nsr:
                raise SecurityResourceValidationException('Could not find resource {}'.format(resource_id))
            if nsr_status == 'ACTIVE':
                log.debug("NSR is active")
                break
            if nsr_status == 'ERROR':
                error_message = 'NSR for resource {} is in ERROR state.'.format(resource_id)
                log.error(error_message)
                vnfr_list = nsr.get('vnfr') or []
                for vnfr in vnfr_list:
                    if vnfr.get('status') == 'ERROR':
                        vnfr_name = vnfr.get('name') or 'COULD NOT GET VNFR NAME'
                        failed_lifecycle_events = vnfr.get('failed lifecycle events') or []
                        if len(failed_lifecycle_events) > 0:
                            log.error(' VNFR {}: {}  '.format(vnfr_name, ' AND '.join(failed_lifecycle_events)))
                raise SecurityResourceValidationException(error_message)

#            for k, v in res.items():
#                if "ERROR" in str(v).upper():
#                    raise SecurityResourceValidationException(v)
#            if res.get('status') == 'ACTIVE':
#                api_url = res.get('api_url')
#                resp = requests.get(api_url)
#                if resp.status_code != 200:
#                    raise SecurityResourceValidationException(resp.text)
#                else:
#                    return
#            time.sleep(3)
#        else:
#            raise SecurityResourceValidationException('Security resource did not reach active state.')

        if not nsr:
            raise SecurityResourceValidationException('Could not find resource {}'.format(resource_id))
