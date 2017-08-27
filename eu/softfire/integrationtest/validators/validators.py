import importlib
import logging
from abc import ABCMeta, abstractmethod

log = logging.getLogger(__name__)
validator_package_name = 'eu.softfire.integrationtest.validators'


class AbstractValidator(metaclass=ABCMeta):
    @abstractmethod
    def validate(self, resource, resource_id, experimenter_name, experimenter_pwd):
        pass


def get_validator(resource_type):
    validator_path = "%s.%s.%sValidator" % (validator_package_name, resource_type, resource_type)
    module_name, class_name = validator_path.rsplit(".", 1)
    validator_class = getattr(importlib.import_module(module_name), class_name)
    return validator_class()
    # validator = importlib.import_module(resource_type + "Validator", validator_package_name)()
    #
    # if resource_type == 'MonitoringResource':
    #     raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    # if resource_type == 'NfvResource':
    #     return NfvResourceValidator()
    # if resource_type == 'SdnResource':
    #     raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    # if resource_type == 'PhysicalResource':
    #     raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    # if resource_type == 'SecurityResource':
    #     raise NotImplementedError('No validator implemented for resources of type {}.'.format(resource_type))
    # raise Exception('Unknown resource type provided: {}'.format(resource_type))


if __name__ == '__main__':
    val = get_validator('NfvResource')
    print(val)
