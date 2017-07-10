import json
import logging
import time
from json import JSONDecodeError

import requests

from eu.softfire.integrationtest.utils.exceptions import MonitoringResourceValidationException
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)


class MonitoringResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id):
        log.debug('Validate MonitoringResource with resource_id: {}'.format(resource_id))
        log.debug('Validate MonitoringResource with resource: {}'.format(resource))
        try:
            res = json.loads(resource)
        except JSONDecodeError as e:
            raise MonitoringResourceValidationException(e.msg)

        cnt = 1
        while True:

            log.debug('Validate attempt: {}'.format(cnt))

            try:
                r = requests.get(res["url"], timeout=10)
                if r.status_code == 200:
                    if "zabbix.php" in r.text:
                        log.debug('********SUCCESSS*********')
                        return
            except Exception as e:
                import traceback
                exception_data = traceback.format_exc().splitlines()
                exception_text = "Error: {}".format(exception_data[-1])
                log.error(exception_text)
                if cnt>3:
                    raise e #raise exceptions only after 3 attempts, to allow test passing in slow environments

            cnt += 1
            if cnt > 4:
                break
            time.sleep(5)

        raise MonitoringResourceValidationException(res)
