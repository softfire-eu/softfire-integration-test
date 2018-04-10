import json
import logging

import requests

from eu.softfire.integrationtest.utils.exceptions import SdnValidationException
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)


class SdnResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id, used_resource_id, session):
        log.debug("Validate SdnResource with id :%s" % resource_id)
        # resource = get_resource_from_id(resource_id) # refresh resource data not needed for static resources
        res_data = json.loads(resource)
        if not res_data:
            raise SdnValidationException('Could not find resource {}'.format(resource_id))

        log.debug("Resource properdies: %s" % res_data)
        res_uri = res_data["URI"]
        res_ftr = res_data["flow-table-range"]
        res_token = res_data["token"]
        if res_uri and res_token and res_ftr:
            # targeturl = urllib.parse.urljoin(res_uri, "api")
            targeturl = res_uri
            payload = {"jsonrpc": "2.0", "method": "list.methods", "params": [], "id": 23}
            try:
                result = requests.post(targeturl, json=payload, headers={'API-Token': res_token})
                if result.status_code == 200:
                    resj = result.json()
                    log.debug("result: %s" % resj)
                    if resj.get("error"):
                        raise SdnValidationException(
                            "JSON rpc returned an error(%s)" % resj.get("error", dict()).get("message", "Unknown"))
                else:
                    raise SdnValidationException("json-rcp api returned status %s" % result.status_code)
            except ValueError as e:
                log.error("invalid json-rpc reply: %s" % e)
                pass
            except Exception as e:
                log.error("json-rpc request to url '%s' failed: %s" % (targeturl, e))
                print("json-rpc request to url '%s' failed: %s" % (targeturl, e))
                raise SdnValidationException(e)


if __name__ == '__main__':
    SdnResourceValidator().validate('''{
    "resource_id": "sdn-controller-opensdncore-fokus",
    "flow-table-range": [
        23,
        24,
        25
    ],
    "URI": "http://172.20.30.5:8001/api",
    "token": "08dc683f45e7d7f59b0a294ca9852b67"
}''', "test")
    print("OK")
