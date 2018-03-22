import json
import logging
import os.path
import sys
import time
import csv
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
EXPERIMENT_BASE_DIR = '/etc/softfire'
EXPERIMENTS = ['fokus', 'ads', 'surrey']
log = get_logger(__name__)
logging.getLogger().setLevel("ERROR")
logging.getLogger(__name__).setLevel("DEBUG")


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
        validation_start = datetime.now()
        try:
            log.debug("started validation phase")
            __validate_experiment_file(os.path.join(EXPERIMENT_BASE_DIR, "monitoring_"+exp+'.csar'))
            validation_end = datetime.now()
        except Exception as e:
            traceback.print_exc()
            log.error('Preparation phase failed.')
            return
        ts_dict[exp]['VALIDATION_TIME'] = validation_end - validation_start
        log.info('Finished validation phase.')

        try:
            upload_start = datetime.now()
            upload_experiment(os.path.join(EXPERIMENT_BASE_DIR, 'monitoring_'+exp+'.csar'), user_session)
            upload_end = datetime.now()
            log.info('Experimenter {} uploaded experiment {}.'.format(USERNAME, exp))
            ts_dict[exp]['UPLOAD_TIME'] = upload_end - upload_start
        except Exception as e:
            log.error('Experimenter {} could not upload experiment {}.'.format(USERNAME, os.path.join(EXPERIMENT_BASE_DIR, "monitoring_"+exp+'.csar')))
            traceback.print_exc()

        try:
            experiment_id = '{}_monitoring_KPI_{}'.format(USERNAME, exp)
            deploy_start = datetime.now()
            log.debug("Starting deploy experiment %s" % experiment_id)
            deploy_experiment(user_session, experiment_id)
            deploy_end = datetime.now()
            ts_dict[exp]['DEPLOY_TIME'] = deploy_end - deploy_start
        except Exception as e:
            log.error('The experiment\'s deployment failed for experimenter {}.'.format(USERNAME))

        deployed_experiment = get_experiment_status(user_session, experiment_id=experiment_id)
        for resource in deployed_experiment:
            used_resource_id = resource.get('used_resource_id')
            resource_id = resource.get('resource_id')
            node_type = resource.get('node_type')
            try:
                log.info("Starting to validate resource of node type: %s" % node_type)
                validator = get_validator("NfvResourceBase")
                log.debug("Got validator %s" % validator)
                booting_start = datetime.now()
                validator.validate(get_resource_from_id(used_resource_id, session=user_session), used_resource_id, user_session)
                booting_end = datetime.now()
                ts_dict[exp]['BOOTING_TIME'] = booting_end - booting_start
                log.info('Validation of resource {}: {}-{} succeeded.'.format(USERNAME, resource_id, used_resource_id))
            except Exception as e:
                error_message = e.message if isinstance(e, IntegrationTestException) else str(e)
                log.error('Validation of resource {}: {}-{} failed: {}'.format(USERNAME, resource_id, used_resource_id, error_message))
                traceback.print_exc()
        log.info('Resource validation phase for {} finished.'.format(experiment_id))

        try:
            log.info("Removing experiment {} of {}".format(experiment_id, USERNAME))
            delete_start = datetime.now()
            delete_experiment(user_session, experiment_id)
            delete_end = datetime.now()
            ts_dict[exp]['DELETE_TIME'] = delete_end - delete_start
            log.info('Removed experiment {} of {}.'.format(experiment_id, USERNAME))
        except Exception as e:
            log.error('Failure during removal of experiment {} of {}.'.format(experiment_id, USERNAME))
            traceback.print_exc()

        ts_dict[exp]['DEPLOY_TOTAL_TIME'] = booting_end - validation_start

    for k in ts_dict['fokus'].keys():
        print("%s - %s" % (k, ts_dict['fokus'][k]))

    for k in ts_dict.keys():
        write_header = False
        if not os.path.exists("%s.csv" % k):
            write_header = True
        with open("%s.csv" % k, 'a') as f:
            if write_header:
                f.write("VALIDATION_TIME,UPLOAD_TIME,DEPLOY_TIME,BOOTING_TIME,DEPLOY_TOTAL_TIME,DELETE_TIME\n")
                f.write("%s,%s,%s,%s,%s,%s\n" % (ts_dict[k]['VALIDATION_TIME'],ts_dict[k]['UPLOAD_TIME'],ts_dict[k]['DEPLOY_TIME'],ts_dict[k]['BOOTING_TIME'],ts_dict[k]['DEPLOY_TOTAL_TIME'],ts_dict[k]['DELETE_TIME'])) 
            else:
                f.write("%s,%s,%s,%s,%s,%s\n" % (ts_dict[k]['VALIDATION_TIME'],ts_dict[k]['UPLOAD_TIME'],ts_dict[k]['DEPLOY_TIME'],ts_dict[k]['BOOTING_TIME'],ts_dict[k]['DEPLOY_TOTAL_TIME'],ts_dict[k]['DELETE_TIME']))


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
