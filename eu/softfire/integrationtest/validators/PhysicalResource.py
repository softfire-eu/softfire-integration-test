from eu.softfire.integrationtest.utils.exceptions import PhysicalResourceValidatorError
from eu.softfire.integrationtest.utils.utils import get_logger
from eu.softfire.integrationtest.validators.validators import AbstractValidator

logger = get_logger(__name__)


class PhysicalResourceValidator(AbstractValidator):
    def validate(self, resource, resource_id, used_resource_id, session):
        if not resource:
            raise PhysicalResourceValidatorError("Resource is none or empty!")
        else:
            logger.info("Resource is %s" % resource)
        logger.info("Nothing to validate here")

        pass
