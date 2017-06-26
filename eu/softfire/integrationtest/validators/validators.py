import json
import logging
import subprocess
import time
from abc import ABCMeta, abstractmethod

from eu.softfire.integrationtest.main.experiment_manager_client import get_experiment_status

log = logging.getLogger(__name__)


class AbstractValidator(metaclass=ABCMeta):
    @abstractmethod
    def validate(self, resource_id):
        pass


class NfvResourceValidator(AbstractValidator):
    def validate(self, resource_id):
        log.debug('Validate NfvResource with resource_id: {}'.format(resource_id))
        # wait at most about 4 minutes for the NSR to reach active state
        for i in range(48):
            time.sleep(5)
            status = get_experiment_status()
            nsr = None
            for resource in status:
                if resource.get('resource_id') == resource_id:
                    # TODO check status
                    value = resource.get('value').strip("'")
                    nsr = json.loads(value)
                    break
            if not nsr:
                raise Exception('Could not find resource {}'.format(resource_id))
            if nsr.get('status') == 'ACTIVE':
                log.debug("NSR is active")
                break
            if nsr.get('status') == 'ERROR':
                error_message = 'NSR for resource {} is in ERROR state.'.format(resource_id)
                log.error(error_message)
                raise Exception(error_message)
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
            raise Exception(error_message)
        if len(pingable_floating_ips) == 0:
            error_message = 'Did not find any floating IP to check.'
            log.error(error_message)
            raise Exception(error_message)
        log.debug('Successfully pinged the following floating IPs: {}'.format(', '.join(pingable_floating_ips)))


def get_validator(resource_type):
    if resource_type == 'MonitoringResource':
        raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    if resource_type == 'NfvResource':
        return NfvResourceValidator()
    if resource_type == 'SdnResource':
        raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    if resource_type == 'PhysicalResource':
        raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    if resource_type == 'SecurityResource':
        raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    raise Exception('Unknown resource type provided: {}'.format(resource_type))
