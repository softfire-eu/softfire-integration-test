#import configparser
import os.path
#import queue
#import sys
#import threading
#import time
import traceback
#import zipfile
#
#import yaml
from collections import OrderedDict
from eu.softfire.integrationtest.main.experiment_manager_client import create_user, upload_experiment, \
    delete_experiment, deploy_experiment, get_resource_from_id, get_experiment_status, delete_user, \
    log_in
#from eu.softfire.integrationtest.utils.exceptions import IntegrationTestException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.utils.utils import get_logger, print_results
from eu.softfire.integrationtest.validators.validators import get_validator
from datetime import datetime

USERNAME = 'test_kpi'
PASSWORD = 'test_kpi'
EXPERIMENT_BASE_DIR = 'csars/monitoring_kpi'
EXPERIMENTS = ['ads', 'ericsson', 'fokus', 'surrey']
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

def start_monitoring_kpi_test():

    log.info("Starting the SoftFIRE integration tests.")
    test_results = OrderedDict()

    # get config values
    exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
    exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
    admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)
    #exp = __get_experimenter()

    try:
        create_user(USERNAME, PASSWORD, 'experimenter', admin_session)
        log.info('Triggered the creation of a new experimenter named \'{}\'.'.format(USERNAME))
    except Exception as e:
        log.error('Could not trigger the creation of a new experimenter named {}.'.format(USERNAME))
        traceback.print_exc()
        add_result(test_results, 'Create User', 'FAILED', '{}: {}'.format(USERNAME, str(e)))

    user_session = log_in(USERNAME, PASSWORD)
    ts_dict = {}

    # validate experiment files (preparation phase)
    for e in EXPERIMENTS:
        ts_dict[e] = {}
        ts_dict[e]["START"] = datetime.now()
        preparation_failed = False
        try:
            __validate_experiment_file(os.path.join(EXPERIMENT_BASE_DIR, e+'.csar'))
            ts_dict[e]["VALIDATION_END"] = datetime.now()
        except Exception as e:
            traceback.print_exc()
            add_result(test_results, 'Preparation', 'FAILED', '{}: {}'.format(USERNAME, str(e)))
            preparation_failed = True
        log.info('Finished preparation phase.')
        if preparation_failed:
            log.error('Preparation phase failed.')
            time.sleep(1)
            print()
            print_results([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])
            __exit_on_failure([[r[0], r[1].get('status'), r[1].get('details')] for r in test_results.items()])
            return

        try:
            ts_dict[e]["UPLOAD_START"] = datetime.now()
            upload_experiment(os.path.join(EXPERIMENT_BASE_DIR, e+'.csar'), user_session)
            ts_dict[e]["UPLOAD_END"] = datetime.now()
            log.info('Experimenter {} uploaded experiment {}.'.format(USERNAME, e))
            add_result(test_results, 'Upload Experiment', 'OK', '')
        except Exception as e:
            log.error('Experimenter {} could not upload experiment {}.'.format(USERNAME, os.path.join(EXPERIMENT_BASE_DIR, e+'.csar')))
            traceback.print_exc()
            add_result(test_results, 'Upload Experiment', 'FAILED', '{}: {}'.format(USERNAME, str(e)))

#        deployment_threads_queues = []
        try:
            experiment_id = '{}_{}'.format(USERNAME, e)
            ts_dict[e]["DEPLOY_START"] = datetime.now()
            deploy_experiment(user_session, experiment_id)
            ts_dict[e]["DEPLOY_END"] = datetime.now()
            add_result(test_results, 'Deploy Experiment', 'OK', '')
        except Exception as e:
            log.error('The experiment\'s deployment failed for experimenter {}.'.format(USERNAME))
            add_result(test_results, 'Deploy Experiment', 'FAILED', '{}: {}'.format(USERNAME, str(e)))


        # validate deployments
#        validated_resources = []
#            failed_resources = []
            deployed_experiment = get_experiment_status(user_session, experiment_id=experiment_id)
            for resource in deployed_experiment:
                used_resource_id = resource.get('used_resource_id')
                resource_id = resource.get('resource_id')
                node_type = resource.get('node_type')
                try:
                    log.info("Starting to validate resource of node type: %s" % node_type)
                    validator = get_validator(node_type)
                    log.debug("Got validator %s" % validator)
                    ts_dict[e]["VALIDATE_START"] = datetime.now()
                    validator.validate(get_resource_from_id(used_resource_id, session=user_session), used_resource_id, user_session)
                    ts_dict[e]["VALIDATE_END"] = datetime.now()
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
            log.info('Resource validation phase for {} finished.'.format(experiment_id))

            try:
                log.info('\n\n\n')
                log.info("Removing experiment {} of {}".format(experiment_id, USERNAME))
                ts_dict[e]["DELETE_START"] = datetime.now()
                delete_experiment(user_session, experiment_id)
                ts_dict[e]["DELETE_END"] = datetime.now()
                log.info('Removed experiment {} of {}.\n\n\n'.format(experiment_id, USERNAME))
                add_result(test_results, 'Delete Experiment', 'OK', '')
            except Exception as e:
                log.error('Failure during removal of experiment {} of {}.'.format(experiment_id, USERNAME))
                traceback.print_exc()
                add_result(test_results, 'Delete Experiment', 'FAILED', '{}: {}'.format(USERNAME, str(e)))

    try:
        delete_user(USERNAME, admin_session)
        log.info('Successfully removed experimenter named \'{}\'.'.format(USERNAME))
        add_result(test_results, 'Delete User', 'OK', '')
    except Exception as e:
        log.error('Could not remove experimenter named {}.'.format(PASSWORD))
        traceback.print_exc()
        add_result(test_results, 'Delete User', 'FAILED', '{}: {}'.format(experimenter_name, str(e)))


    print(ts_dict)

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
    experimenter_name = get_config_value('experimenter', 'username')
    experimenter_password = get_config_value('experimenter', 'password')
    experiment_file = get_config_value('experimenter', 'experiment')
    experiment_name = get_config_value('experimenter', 'experiment-name')
    exp = {'experimenter_name': experimenter_name, 'experimenter_password': experimenter_password, 'experiment_file': experiment_file, 'experiment_name': experiment_name}

    return exp
