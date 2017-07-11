import os.path
import sys
import time
import traceback
import zipfile

import yaml

from eu.softfire.integrationtest.main.experiment_manager_client import create_user, upload_experiment, \
    delete_experiment, deploy_experiment, get_resource_from_id, get_experiment_status
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.utils.utils import get_logger, print_results
from eu.softfire.integrationtest.validators.validators import get_validator

log = get_logger(__name__)


def start_integration_test():
    log.info("Starting the SoftFIRE integration tests.")
    test_results = []

    # get config values
    exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
    exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
    experimenter_name = get_config_value('experimenter', 'username')
    experimenter_password = get_config_value('experimenter', 'password')
    experiment_file_path = get_config_value('experiment', 'experiment-file')

    # retrieve information from experiment file (preparation phase)
    try:
        experiment_resources = __get_experiment_resources(experiment_file_path)
        log.info('Finished preparation phase.')
    except Exception as e:
        traceback.print_exc()
        test_results.append(['Preparation', 'FAILED', str(e)])
        time.sleep(1)
        print()
        print_results(test_results)
        __exit_on_failure(test_results)
        return

    # create experimenter
    if get_config_value('experimenter', 'create-user', 'True') in ['True', 'true']:
        try:
            create_user(experimenter_name, experimenter_password, 'experimenter',
                        executing_user_name=exp_mngr_admin_name, executing_user_pwd=exp_mngr_admin_pwd)
            log.info('Successfully created a new experimenter named \'{}\'.'.format(experimenter_name))
            test_results.append(['Create User', 'OK', ''])
        except Exception as e:
            log.error('Could not create experimenter named {}.'.format(experimenter_name))
            traceback.print_exc()
            test_results.append(['Create User', 'FAILED', str(e)])

    try:
        upload_experiment(experiment_file_path)
        log.info('Uploaded experiment {}.'.format(experiment_file_path))
        test_results.append(['Upload Experiment', 'OK', ''])
    except Exception as e:
        log.error('Could not upload experiment {}.'.format(experiment_file_path))
        traceback.print_exc()
        test_results.append(['Upload Experiment', 'FAILED', str(e)])

    try:
        deploy_experiment()
        log.info('Deployed experiment.\n\n\n')
        time.sleep(5)
        test_results.append(['Deploy Experiment', 'OK', ''])
    except Exception as e:
        log.error('The experiment\'s deployment failed.')
        traceback.print_exc()
        test_results.append(['Deploy Experiment', 'FAILED', str(e)])

    # validate deployment
    validated_resources = []
    failed_resources = []
    deployed_experiment = get_experiment_status()
    for resource in deployed_experiment:
        used_resource_id = resource.get('used_resource_id')
        resource_id = resource.get('resource_id')
        node_type = resource.get('node_type')
        try:
            log.info("Starting to validate resource of node type: %s" % node_type)
            validator = get_validator(node_type)
            log.debug("Got validator %s" % validator)
            validator.validate(get_resource_from_id(used_resource_id), used_resource_id)
            log.info('\n\n\n')
            log.info('Validation of resource {}-{} succeeded.\n\n\n'.format(resource_id, used_resource_id))
            time.sleep(5)
            validated_resources.append(['   - {}-{}'.format(resource_id, used_resource_id), 'OK', ''])
        except Exception as e:
            log.error('Validation of resource {}-{} failded.'.format(resource_id, used_resource_id))
            traceback.print_exc()
            validated_resources.append(['   - {}-{}'.format(resource_id, used_resource_id), 'FAILED', str(e)])
            failed_resources.append(resource_id)
    if len(failed_resources) == 0:
        test_results.append(['Validate Resources', 'OK', ''])
    else:
        test_results.append(['Validate Resources', 'FAILED', ', '.join(failed_resources)])
    test_results = test_results + validated_resources
    log.info('Resource validation phase finished with {} validated resource{}.'.format(len(validated_resources), (
        '' if len(validated_resources) == 1 else 's')))

    try:
        log.info('\n\n\n')
        log.info("Removing Experiment")
        delete_experiment()
        log.info('Removed experiment.\n\n\n')
        test_results.append(['Delete Experiment', 'OK', ''])
    except Exception as e:
        log.error('Failure during removal of experiment.')
        traceback.print_exc()
        test_results.append(['Delete Experiment', 'FAILED', str(e)])

    time.sleep(1)  # otherwise the results were printed in the middle of the stack traces
    print()
    print_results(test_results)
    __exit_on_failure(test_results)


def __get_experiment_resources(experiment_file_path):
    experiment_resources = {}
    if not os.path.isfile(experiment_file_path):
        raise FileNotFoundError('Experiment file {} not found'.format(experiment_file_path))
    with zipfile.ZipFile(experiment_file_path) as zf:
        with zf.open('Definitions/experiment.yaml') as experiment_yaml:
            experiment_yaml_dict = yaml.safe_load(experiment_yaml)
            topology_template = experiment_yaml_dict.get('topology_template')
            if not topology_template:
                raise Exception('The experiment\'s experiment.yaml file misses the topology_template item.')
            node_templates = topology_template.get('node_templates')
            if not node_templates:
                raise Exception('The experiment\'s experiment.yaml file misses the node_templates item.')
            for node_key in node_templates:
                node = node_templates.get(node_key)
                resource_type = node.get('type')
                node_properties = node.get('properties')
                if not node_properties:
                    raise Exception(
                        'The experiment\'s experiment.yaml file contains a node_template without properties.')
                resource_id = node_properties.get('resource_id')
                if not resource_id:
                    raise Exception('Could not retrieve the resource_id of node {}'.format(node_key))
                if not resource_type:
                    raise Exception('Could not retrieve the type of node {}'.format(node_key))
                experiment_resources[resource_id] = resource_type
    return experiment_resources


def __exit_on_failure(test_results):
    for result in [r[1] for r in test_results]:
        if result != 'OK':
            sys.exit(1)
