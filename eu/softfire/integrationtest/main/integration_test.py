import configparser
import os.path
import queue
import sys
import threading
import time
import traceback
import zipfile

import yaml
from collections import OrderedDict
from eu.softfire.integrationtest.main.experiment_manager_client import create_user, upload_experiment, \
    delete_experiment, deploy_experiment, get_resource_from_id, get_experiment_status, delete_user, \
    log_in
from eu.softfire.integrationtest.utils.exceptions import IntegrationTestException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.utils.utils import get_logger, print_results
from eu.softfire.integrationtest.validators.validators import get_validator

log = get_logger(__name__)



def add_result(result_dict, phase, status, details):
    if phase not in result_dict:
        result_dict[phase] = {'status': status, 'details': details}
        return
    res = result_dict.get(phase)
    if status != 'OK':
        res['status'] = status
    if details != '':
        res['details'] = '{}; {}'.format(res.get('details'), details) if res.get('details') is not None and res.get('details') != '' else details

def start_integration_test():
    log.info("Starting the SoftFIRE integration tests.")
    test_results = OrderedDict()

    # get config values
    exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
    exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
    admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)
    experimenters = __get_experimenters()

    # validate experiment files (preparation phase)
    preparation_failed = False
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experiment_file = experimenter[4]
        try:
            __validate_experiment_file(experiment_file)
        except Exception as e:
            traceback.print_exc()
            add_result(test_results, 'Preparation', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))
            preparation_failed = True
    log.info('Finished preparation phase.')
    if preparation_failed:
        log.error('Preparation phase failed.')
        time.sleep(1)
        print()
        print_results([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])
        __exit_on_failure([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])
        return

    # create experimenter(s)
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        create_experimenter = experimenter[2]
        if create_experimenter in ['True', 'true']:
            try:
                create_user(experimenter_name, experimenter_pwd, 'experimenter', admin_session)
                log.info('Triggered the creation of a new experimenter named \'{}\'.'.format(experimenter_name))
            except Exception as e:
                log.error('Could not trigger the creation of a new experimenter named {}.'.format(experimenter_pwd))
                traceback.print_exc()
                add_result(test_results, 'Create User', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))

    # check if the users were created correctly
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        create_experimenter = experimenter[2]
        if create_experimenter in ['True', 'true']:
            log.debug('Trying to log in as user {} to check if the user was created successfully.'.format(experimenter_name))
            for i in range(0, 18):
                time.sleep(5)
                try:
                    log_in(experimenter_name, experimenter_pwd)
                    add_result(test_results, 'Create User', 'OK', '')
                    break
                except:
                    pass
            else:
                log.error('Not able to log in as experimenter {}. Assuming the creation failed.')
                add_result(test_results, 'Create User', 'FAILED',
                           '{}: The user seems not to exist.'.format(experimenter_name))

    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_file = experimenter[4]
        user_session = log_in(experimenter_name, experimenter_pwd)
        try:
            upload_experiment(experiment_file, user_session)
            log.info('Experimenter {} uploaded experiment {}.'.format(experimenter_name, experiment_file))
            add_result(test_results, 'Upload Experiment', 'OK', '')
        except Exception as e:
            log.error('Experimenter {} could not upload experiment {}.'.format(experimenter_name, experiment_file))
            traceback.print_exc()
            add_result(test_results, 'Upload Experiment', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))

    deployment_threads_queues = []
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_name = experimenter[5]
        experiment_id = '{}_{}'.format(experimenter_name, experiment_name)
        user_session = log_in(experimenter_name, experimenter_pwd)
        q = queue.Queue()
        t = threading.Thread(target=deploy_experiment, args=(user_session, experiment_id, q,), name=experimenter_name)
        deployment_threads_queues.append((t, q))
    for (t, q) in deployment_threads_queues:
        log.info('Deploy experiment of experimenter {}'.format(t.name))
        t.start()
    time.sleep(5)
    for (t, q) in deployment_threads_queues:
        t.join()
        exception = q.get()
        if exception is not None:
            log.error('The experiment\'s deployment failed for experimenter {}.'.format(t.name))
            add_result(test_results, 'Deploy Experiment', 'FAILED', '{}: {}'.format(t.name, str(exception)))
        else:
            add_result(test_results, 'Deploy Experiment', 'OK', '')

    # validate deployments
    validated_resources = []
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_name = experimenter[5]
        experiment_id = '{}_{}'.format(experimenter_name, experiment_name)
        failed_resources = []
        user_session = log_in(experimenter_name, experimenter_pwd)
        deployed_experiment = get_experiment_status(user_session, experiment_id=experiment_id)
        for resource in deployed_experiment:
            used_resource_id = resource.get('used_resource_id')
            resource_id = resource.get('resource_id')
            node_type = resource.get('node_type')
            try:
                log.info("Starting to validate resource of node type: %s" % node_type)
                validator = get_validator(node_type)
                log.debug("Got validator %s" % validator)
                validator.validate(get_resource_from_id(used_resource_id, session=user_session), resource_id, used_resource_id, user_session)
                log.info('\n\n\n')
                log.info('Validation of resource {}: {}-{} succeeded.\n\n\n'.format(experimenter_name, resource_id, used_resource_id))
                time.sleep(5)
                validated_resources.append(['   - {}: {}-{}'.format(experimenter_name, resource_id, used_resource_id), 'OK', ''])
            except Exception as e:
                error_message = e.message if isinstance(e, IntegrationTestException) else str(e)
                log.error('Validation of resource {}: {}-{} failed: {}'.format(experimenter_name, resource_id, used_resource_id, error_message))
                traceback.print_exc()
                validated_resources.append(['   - {}: {}-{}'.format(experimenter_name, resource_id, used_resource_id), 'FAILED', '{}: {}'.format(experimenter_name, error_message)])
                failed_resources.append(resource_id)
        if len(failed_resources) == 0:
            add_result(test_results, 'Validate Resources', 'OK', '')
        else:
            add_result(test_results, 'Validate Resources', 'FAILED', '{}: {}'.format(experimenter_name, ', '.join(failed_resources)))
        log.info('Resource validation phase for {} finished.'.format(experimenter_name))
    for resource in validated_resources:
        add_result(test_results, resource[0], resource[1], resource[2])

    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_name = experimenter[5]
        experiment_id = '{}_{}'.format(experimenter_name, experiment_name)
        user_session = log_in(experimenter_name, experimenter_pwd)
        try:
            log.info('\n\n\n')
            log.info("Removing experiment {} of {}".format(experiment_id, experimenter_name))
            delete_experiment(user_session, experiment_id)
            log.info('Removed experiment {} of {}.\n\n\n'.format(experiment_id, experimenter_name))
            add_result(test_results, 'Delete Experiment', 'OK', '')
        except Exception as e:
            log.error('Failure during removal of experiment {} of {}.'.format(experiment_id, experimenter_name))
            traceback.print_exc()
            add_result(test_results, 'Delete Experiment', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))

    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        delete_experimenter = experimenter[3]
        if delete_experimenter in ['True', 'true']:
            try:
                delete_user(experimenter_name, admin_session)
                log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
                add_result(test_results, 'Delete User', 'OK', '')
            except Exception as e:
                log.error('Could not remove experimenter named {}.'.format(experimenter_pwd))
                traceback.print_exc()
                add_result(test_results, 'Delete User', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))


    time.sleep(1)  # otherwise the results were printed in the middle of the stack traces
    print()
    print_results([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])
    __exit_on_failure([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])


def __validate_experiment_file(experiment_file_path):
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


def __exit_on_failure(test_results):
    for result in [r[1] for r in test_results]:
        if result != 'OK':
            sys.exit(1)


def __get_experimenters():
    """
    Get the experimenters defined in the integration test configuration file.
    You can specify just one experimenter with a section called [experimenter]
    or you can add additional ones by using sections called [experimenter-x] where x is an integer between 0 and 99.
    In any case the experimenter in section [experimenter] has to be present always.
    :return:
    """
    experimenter_name = get_config_value('experimenter', 'username')
    experimenter_password = get_config_value('experimenter', 'password')
    create_experimenter = get_config_value('experimenter', 'create-user', 'True')
    delete_experimenter = get_config_value('experimenter', 'delete-user', 'True')
    experiment_file = get_config_value('experimenter', 'experiment')
    experiment_name = get_config_value('experimenter', 'experiment-name')
    experimenters = [(experimenter_name, experimenter_password, create_experimenter, delete_experimenter, experiment_file, experiment_name)]
    for i in range(0, 100):
        try:
            experimenter_name = get_config_value('experimenter-{}'.format(i), 'username')
            experimenter_password = get_config_value('experimenter-{}'.format(i), 'password')
            create_experimenter = get_config_value('experimenter-{}'.format(i), 'create-user', 'True')
            delete_experimenter = get_config_value('experimenter-{}'.format(i), 'delete-user', 'True')
            experiment_file = get_config_value('experimenter-{}'.format(i), 'experiment')
            experiment_name = get_config_value('experimenter-{}', 'experiment-name')
            experimenters.append((experimenter_name, experimenter_password, create_experimenter, delete_experimenter, experiment_file, experiment_name))
        except (configparser.NoSectionError, configparser.NoOptionError):
            break
    return experimenters