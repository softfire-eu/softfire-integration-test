import json
import logging
import subprocess
import time

from eu.softfire.integrationtest.main.experiment_manager_client import get_resource_from_id
from eu.softfire.integrationtest.utils.exceptions import NfvValidationException
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)


class NfvResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id):
        log.debug('Validate NfvResource with resource_id: {}'.format(resource_id))
        # wait at most about 4 minutes for the NSR to reach active state
        for i in range(48):
            time.sleep(5)
            nsr = None
            # TODO check status
            resource = get_resource_from_id(resource_id)
            nsr = json.loads(resource)

            if not nsr:
                raise NfvValidationException('Could not find resource {}'.format(resource_id))
            if nsr.get('status') == 'ACTIVE':
                log.debug("NSR is active")
                break
            if nsr.get('status') == 'ERROR':
                error_message = 'NSR for resource {} is in ERROR state.'.format(resource_id)
                log.error(error_message)
                raise NfvValidationException(error_message)
        if nsr.get('status') != 'ACTIVE':
            error_message = 'Timeout: the NSR {} is still not in active state'.format(nsr.get('name'))
            log.error(error_message)
            raise NfvValidationException(error_message)
        vnfr_list = nsr.get('vnfr')
        unpingable_floating_ips = []
        pingable_floating_ips = []
        for vnfr in vnfr_list:
            log.debug('Checking VNFR {}.'.format(vnfr.get('name')))
            vdu_list = vnfr.get('vdu')
            for vdu in vdu_list:
                vnfc_instance_list = vdu.get('vnfc_instance')
                for vnfc_instance in vnfc_instance_list:
                    connection_point_list = vnfc_instance.get('connection_point')
                    for connection_point in connection_point_list:
                        floaing_ip = connection_point.get('floatingIp')
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
