import json
import logging
import time
import traceback
from json import JSONDecodeError

import requests

from eu.softfire.integrationtest.utils.exceptions import MonitoringResourceValidationException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)

class MonitoringResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id, session):
        log.debug('Validate MonitoringResource with resource_id: {}'.format(resource_id))
        log.debug('Validate MonitoringResource with resource: {}'.format(resource))

        attempts = int(get_config_value('monitoring-resource', 'attempts', '10'))

        try:
            res = json.loads(resource)
        except JSONDecodeError as e:
            raise MonitoringResourceValidationException(e.msg)

        if not res["floatingIp"]:
            raise MonitoringResourceValidationException("Floating ip not available: {}".format(res))
            
        cnt = 1
        while cnt <= attempts:

            log.debug('Validate attempt: {}'.format(cnt))

            try:
                r = requests.get(res["url"], timeout=10)
                if r.status_code == 200:
                    if "zabbix.php" in r.text:
                        log.debug('********SUCCESSS*********')
                        return
            except Exception as e:
                if cnt > attempts:
                    log.error("after %d attempts zabbix is not started yet, considering it failed..." % attempts)
                    exception_data = traceback.format_exc().splitlines()
                    exception_text = "Error: {}".format(exception_data[-1])
                    log.error(exception_text)
                    raise e  # raise exceptions only after X attempts, to allow test passing in slow environments

            cnt += 1

            time.sleep(5)

        raise MonitoringResourceValidationException(res)
