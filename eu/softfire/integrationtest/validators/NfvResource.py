import json
import subprocess
import time

from eu.softfire.integrationtest.main.experiment_manager_client import get_resource_from_id
from eu.softfire.integrationtest.utils.exceptions import NfvValidationException
from eu.softfire.integrationtest.utils.utils import get_config_value, get_logger
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = get_logger(__name__)

wait_nfv_resource_minuties = int(get_config_value('nfv-resource', 'wait-nfv-res-min', '7'))


class NfvResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id, experimenter_name, experimenter_pwd):
        log.debug('Validate NfvResource with resource_id: {}'.format(resource_id))
        # wait at most about 7 minutes for the NSR to reach active state
        nsr = None
        for i in range(wait_nfv_resource_minuties * 20):
            time.sleep(3)
            resource = get_resource_from_id(resource_id, experimenter_name, experimenter_pwd)
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

        vnfr_list = nsr.get('vnfr')
        unpingable_floating_ips = []
        pingable_floating_ips = []

        for vnfr in vnfr_list:
            log.debug('Checking VNFR {}.'.format(vnfr.get('name')))
            fips = [fip.split(":")[1] for fip in vnfr.get('floating IPs')]
            for floaing_ip in fips:
                log.debug('Checking floating IP {}.'.format(floaing_ip))
                if floaing_ip:
                    ping = subprocess.Popen(
                        ["ping", "-c", "4", floaing_ip],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    out, error = ping.communicate()
                    if error.decode('UTF-8') != '':
                        unpingable_floating_ips.append(floaing_ip)
                    else:
                        pingable_floating_ips.append(floaing_ip)
        if len(unpingable_floating_ips) != 0:
            error_message = 'Could not ping the following floating IPs: {}'.format(', '.join(unpingable_floating_ips))
            log.error(error_message)
            raise NfvValidationException(error_message)
        if len(pingable_floating_ips) == 0:
            error_message = 'Did not find any floating IP to check.'
            log.error(error_message)
            raise NfvValidationException(error_message)
        log.debug('Successfully pinged the following floating IPs: {}'.format(', '.join(pingable_floating_ips)))
