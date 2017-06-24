import json
import os

import requests
from eu.softfire.integrationtest.utils.utils import get_logger
from eu.softfire.integrationtest.utils.utils import get_config_value

experiment_manager_ip = get_config_value('experiment-manager', 'ip', 'localhost')
experiment_manager_port = get_config_value('experiment-manager', 'port', '5080')
experiment_manager_login_url = 'http://{}:{}/login'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_create_user_url = 'http://{}:{}/create_user'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_upload_experiment_url = 'http://{}:{}/reserve_resources'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_deploy_experiment_url = 'http://{}:{}/provide_resources'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_delete_experiment_url = 'http://{}:{}/release_resources'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_get_status_url = 'http://{}:{}/get_status'.format(experiment_manager_ip, experiment_manager_port)

log = get_logger(__name__)


def __determine_executing_user(executing_user_name, executing_user_pwd):
    """
    Auxiliary method for retrieving the user credentials that shall be used.
    :param executing_user_name:
    :param executing_user_pwd:
    :return:
    """
    if not executing_user_name:
        executing_user_name = get_config_value('experimenter', 'username')
    if not executing_user_pwd:
        executing_user_pwd = get_config_value('experimenter', 'password')
    return executing_user_name, executing_user_pwd


def __validate_response_status(response_status, expected_status, error_message=None):
    if response_status != expected_status:
        log.error('HTTP response status code was {}, but expected was {}.'.format(response_status, expected_status) or error_message)
        raise Exception


def log_in(username, password):
    """
    Returns a Session object from the requests module on which the user has logged into the experiment manager.
    :param username:
    :param password:
    :return:
    """
    session = requests.Session()
    try:
        log_in_response = session.post(experiment_manager_login_url, data={'username': username, 'password': password})
        __validate_response_status(log_in_response.status_code, 200,
                                   'experiment-manager log in failed for user {}. HTTP response status code was {}, but expected was {}.'.format(
                                       username, log_in_response.status_code, 200))
        response_text_dict = json.loads(log_in_response.text)
        if (not response_text_dict.get('ok')) or response_text_dict.get('ok') == False:
            log.error('experiment-manager log in failed: {}'.format(response_text_dict.get('msg')))
            raise Exception('experiment-manager log in failed: {}'.format(response_text_dict.get('msg')))
    except ConnectionError as ce:
        log.error("Could not connect to the experiment-manager for logging in.")
        raise ce
    except Exception as e:
        log.error('Exception while logging into the experiment manager.')
        raise e
    return session


def create_user(new_user_name, new_user_pwd, new_user_role, executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_create_user_url, data={'username': new_user_name, 'password': new_user_pwd, 'role': new_user_role})
    __validate_response_status(response.status_code, 200)

def upload_experiment(experiment_file_path, executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    if not os.path.isfile(experiment_file_path):
        raise Exception('Experiment file {} not found'.format(experiment_file_path))
    with open(experiment_file_path, 'rb') as experiment_file:
        session = log_in(executing_user_name, executing_user_pwd)
        response = session.post(experiment_manager_upload_experiment_url, files={'data': experiment_file})
    __validate_response_status(response.status_code, 200)

def deploy_experiment(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_deploy_experiment_url)
    __validate_response_status(response.status_code, 200)

def delete_experiment(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_delete_experiment_url)
    __validate_response_status(response.status_code, 200)

def get_status(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.get(experiment_manager_get_status_url)
    __validate_response_status(response.status_code, 200)
    return json.loads(response.text)