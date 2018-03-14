#import configparser
import json
import logging
import os.path
#import queue
import sys
#import threading
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
from datetime import datetime

USERNAME = 'test_kpi'
PASSWORD = 'test_kpi'
EXPERIMENT_BASE_DIR = 'csars/monitoring_kpi'
EXPERIMENTS = ['fokus', 'ads', 'ericsson', 'surrey']
log = get_logger(__name__)
logging.getLogger().setLevel("ERROR")
logging.getLogger(__name__).setLevel("DEBUG")
#logging.getLogger('eu.softfire.integrationtest.main.experiment_manager_client').setLevel("DEBUG")


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

    exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
    exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
    admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)

    user_session = log_in(USERNAME, PASSWORD)
    ts_dict = {}

    for exp in EXPERIMENTS:
        ts_dict[exp] = {}
        ts_dict[exp]["START"] = datetime.now()
        preparation_failed = False
        try:
            log.debug("started validation phase")
            __validate_experiment_file(os.path.join(EXPERIMENT_BASE_DIR, exp+'.csar'))
            ts_dict[exp]["VALIDATION_END"] = datetime.now()
        except Exception as e:
            traceback.print_exc()
            preparation_failed = True
        log.info('Finished validation phase.')
        if preparation_failed:
            log.error('Preparation phase failed.')
            time.sleep(1)
            return

        try:
            ts_dict[exp]["UPLOAD_START"] = datetime.now()
            upload_experiment(os.path.join(EXPERIMENT_BASE_DIR, exp+'.csar'), user_session)
            ts_dict[exp]["UPLOAD_END"] = datetime.now()
            log.info('Experimenter {} uploaded experiment {}.'.format(USERNAME, exp))
        except Exception as e:
            log.error('Experimenter {} could not upload experiment {}.'.format(USERNAME, os.path.join(EXPERIMENT_BASE_DIR, exp+'.csar')))
            traceback.print_exc()

        try:
            experiment_id = '{}_monitoring_KPI_{}'.format(USERNAME, exp)
            log.debug("Starting deploy experiment %s" % experiment_id)
            ts_dict[exp]["DEPLOY_START"] = datetime.now()
            deploy_experiment(user_session, experiment_id)
            ts_dict[exp]["DEPLOY_END"] = datetime.now()
        except Exception as e:
            log.error('The experiment\'s deployment failed for experimenter {}.'.format(USERNAME))

        time.sleep(3)
        deployed_experiment = get_experiment_status(user_session, experiment_id=experiment_id)
        print(deployed_experiment)
        for resource in deployed_experiment:
            continue
            used_resource_id = resource.get('used_resource_id')
            resource_id = resource.get('resource_id')
            node_type = resource.get('node_type')
            try:
                log.info("Starting to validate resource of node type: %s" % node_type)
                validator = get_validator(node_type)
                log.debug("Got validator %s" % validator)
                ts_dict[exp]["VALIDATE_START"] = datetime.now()
                validator.validate(get_resource_from_id(used_resource_id, session=user_session), used_resource_id, user_session)
                ts_dict[exp]["VALIDATE_END"] = datetime.now()
                log.info('\n\n\n')
                log.info('Validation of resource {}: {}-{} succeeded.'.format(USERNAME, resource_id, used_resource_id))
                time.sleep(5)
                validated_resources.append(['   - {}: {}-{}'.format(experimenter_name, resource_id, used_resource_id), 'OK', ''])
            except Exception as e:
                error_message = e.message if isinstance(e, IntegrationTestException) else str(e)
                log.error('Validation of resource {}: {}-{} failed: {}'.format(USERNAME, resource_id, used_resource_id, error_message))
                traceback.print_exc()
        log.info('Resource validation phase for {} finished.'.format(experiment_id))

        try:
            log.info("Removing experiment {} of {}".format(experiment_id, USERNAME))
            ts_dict[exp]["DELETE_START"] = datetime.now()
            delete_experiment(user_session, experiment_id)
            ts_dict[exp]["DELETE_END"] = datetime.now()
            log.info('Removed experiment {} of {}.'.format(experiment_id, USERNAME))
        except Exception as e:
            log.error('Failure during removal of experiment {} of {}.'.format(experiment_id, USERNAME))
            traceback.print_exc()

        break

    try:
        with open("./result_KPI.json", 'r') as f:
            old_tests = json.loads(f.read())
    except Exception:
        old_tests = {}

    try:
        old_tests["res_l"].append(ts_dict)
    except Exception:
        old_tests["res_l"] = []
        old_tests["res_l"].append(ts_dict)

    with open("./result_KPI.json", "w") as f:
        f.write(json.dumps(old_tests, default=lambda obj: isinstance(obj, datetime) and obj.__str__()) or obj)


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


def add_experimenter(username, password, admin_session):
    try:
        create_user(username, password, 'experimenter', admin_session)
        log.info('Triggered the creation of a new experimenter named \'{}\'.'.format(username))
    except Exception as e:
        log.error('Could not trigger the creation of a new experimenter named {}.'.format(username))
        traceback.print_exc()

def delete_experimenter(username, admin_session):
    try:
        delete_user(username, admin_session)
        log.info('Successfully removed experimenter named \'{}\'.'.format(username))
    except Exception as e:
        log.error('Could not remove experimenter named {}.'.format(PASSWORD))
        traceback.print_exc()
