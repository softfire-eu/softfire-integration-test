import json
import logging

import requests

from eu.softfire.integrationtest.utils.exceptions import SdnValidationException
from eu.softfire.integrationtest.validators.validators import AbstractValidator

log = logging.getLogger(__name__)


class SdnResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id):
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
                result = requests.post(targeturl, json=payload)
                if result.status_code == 200:
                    resj = result.json()
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
                raise SdnValidationException(e)
