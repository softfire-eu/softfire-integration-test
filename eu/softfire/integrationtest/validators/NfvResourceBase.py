import json
import subprocess
import time

from eu.softfire.integrationtest.main.experiment_manager_client import get_resource_from_id
from eu.softfire.integrationtest.utils.exceptions import NfvValidationException
from eu.softfire.integrationtest.utils.utils import get_config_value, get_logger
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = get_logger(__name__)

wait_nfv_resource_minuties = int(get_config_value('nfv-resource', 'wait-nfv-res-min', '7'))


class NfvResourceBaseValidator(AbstractValidator):
    def validate(self, resource, resource_id, session):
        log.debug('Validate NfvResource with resource_id: {}'.format(resource_id))
        # wait at most about 7 minutes for the NSR to reach active state
        nsr = None
        for i in range(wait_nfv_resource_minuties * 20):
            time.sleep(3)
            resource = get_resource_from_id(resource_id, session)
            try:
                nsr = json.loads(resource)
            except Exception as e:
                log.error('Not able to parse resource: {}'.format(resource))
                raise NfvValidationException('Not able to parse resource: {}'.format(resource))
            nsr_status = nsr.get('status')
            log.debug("Status of nsr is %s" % nsr_status)
            if not nsr:
                raise NfvValidationException('Could not find resource {}'.format(resource_id))
            if nsr_status == 'ACTIVE':
                log.debug("NSR is active")
                break
            if nsr_status == 'ERROR':
                error_message = 'NSR for resource {} is in ERROR state.'.format(resource_id)
                log.error(error_message)
                raise NfvValidationException(error_message)

        if not nsr:
            raise NfvValidationException('Could not find resource {}'.format(resource_id))

        if nsr.get('status') != 'ACTIVE':
            error_message = 'Timeout: the NSR {} is still not in active state after {} minutes'.format(nsr.get('name'),
                                                                                                       wait_nfv_resource_minuties)
            log.error(error_message)
            raise NfvValidationException(error_message)