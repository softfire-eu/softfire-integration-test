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
    delete_experiment, get_resource_from_id, get_experiment_status, delete_user, \
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

def start_ue_resv_engine_test():
    log.info("Starting the SoftFIRE UE reservation engine test.")
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

    # upload experiment
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_file = experimenter[4] # defined in config
        experiment_name = experimenter[5]
        user_session = log_in(experimenter_name, experimenter_pwd)
        try:
            upload_experiment(experiment_file, user_session)
            log.info('Experimenter {} uploaded experiment {}.'.format(experimenter_name, experiment_file))
            add_result(test_results, 'Upload Experiment', 'OK', '')
        except Exception as e:
            log.error('Experimenter {} could not upload experiment {}.'.format(experimenter_name, experiment_file))
            traceback.print_exc()
            add_result(test_results, 'Upload Experiment', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))

    # delete experiment
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        experiment_name = experimenter[5]
        experiment_id = '{}_{}'.format(experimenter_name, experiment_name)
        user_session = log_in(experimenter_name, experimenter_pwd)
        try:
            log.info('\n\n\n')
            log.info("Removing Experiment of {}".format(experimenter_name))
            delete_experiment(user_session, experiment_id)
            log.info('Removed experiment of {}.\n\n\n'.format(experimenter_name))
            add_result(test_results, 'Delete Experiment', 'OK', '')
        except Exception as e:
            log.error('Failure during removal of experiment of {}.'.format(experimenter_name))
            traceback.print_exc()
            add_result(test_results, 'Delete Experiment', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))

    # delete experimenter
    for experimenter in experimenters:
        experimenter_name = experimenter[0]
        experimenter_pwd = experimenter[1]
        delete_experimenter = experimenter[3]
        try_count = 3
        if delete_experimenter in ['True', 'true']:
            while try_count > 0:
                try:
                    delete_user(experimenter_name, admin_session)
                    log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
                    add_result(test_results, 'Delete User', 'OK', '')
                    try_count = 0
                except Exception as e:
                    log.error('Could not remove experimenter named {}.'.format(experimenter_pwd))
                    traceback.print_exc()
                    add_result(test_results, 'Delete User', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))
                    try_count -= 1


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
    Get the ue-test experimenter defined in the integration test configuration file
    :return:
    """
    experimenter_name = get_config_value('ue-test', 'username')
    experimenter_password = get_config_value('ue-test', 'password')
    create_experimenter = get_config_value('ue-test', 'create-user', 'True')
    delete_experimenter = get_config_value('ue-test', 'delete-user', 'True')
    experiment_file = get_config_value('ue-test', 'experiment')
    experiment_name = get_config_value('ue-test', 'experiment-name')
    experimenters = [(experimenter_name, experimenter_password, create_experimenter, delete_experimenter, experiment_file, experiment_name)]
    return experimenters