import json
import os
import traceback

import requests

from eu.softfire.integrationtest.utils.exceptions import IntegrationTestException
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.utils.utils import get_logger

experiment_manager_ip = get_config_value('experiment-manager', 'ip', 'localhost')
experiment_manager_port = get_config_value('experiment-manager', 'port', '5080')
experiment_manager_login_url = 'http://{}:{}/login'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_create_user_url = 'http://{}:{}/create_user'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_upload_experiment_url = 'http://{}:{}/reserve_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
experiment_manager_deploy_experiment_url = 'http://{}:{}/provide_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
experiment_manager_delete_experiment_url = 'http://{}:{}/release_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
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
        error_message = 'HTTP response status code was {}, but expected was {}.'.format(response_status,
                                                                                        expected_status) or error_message
        log.error(error_message)
        raise Exception(error_message)


def log_in(username, password):
    """
    Returns a Session object from the requests module on which the user has logged into the experiment manager.
    :param username:
    :param password:
    :return:
    """
    log.debug('Try to log into the experiment-manager as user \'{}\'.'.format(username))
    session = requests.Session()
    try:
        log_in_response = session.post(experiment_manager_login_url, data={'username': username, 'password': password})
        __validate_response_status(log_in_response.status_code, 200,
                                   'experiment-manager log in failed for user {}. HTTP response status code was {}, but expected was {}.'.format(
                                       username, log_in_response.status_code, 200))
        response_text_dict = json.loads(log_in_response.text)
        if (not response_text_dict.get('ok')) or response_text_dict.get('ok') == False:
            error_message = 'experiment-manager log in failed: {}'.format(response_text_dict.get('msg'))
            log.error(error_message)
            raise Exception(error_message)
    except ConnectionError as ce:
        error_message = 'Could not connect to the experiment-manager for logging in.'
        log.error(error_message)
        traceback.print_exc()
        raise Exception(error_message)
    except Exception as e:
        error_message = 'Exception while logging into the experiment manager.'
        log.error(error_message)
        traceback.print_exc()
        raise Exception(error_message)
    log.debug('Log in succeeded for user {}.'.format(username))
    return session


def create_user(new_user_name, new_user_pwd, new_user_role, executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    log.debug('Try to create a new user named \'{}\' as user \'{}\'.'.format(new_user_name, executing_user_name))
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_create_user_url,
                            data={'username': new_user_name, 'password': new_user_pwd, 'role': new_user_role})
    __validate_response_status(response.status_code, 200)
    log.debug('Creation of a new user named \'{}\' succeeded.'.format(new_user_name))


def upload_experiment(experiment_file_path, executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    log.debug('Try to upload experiment as user \'{}\'.'.format(executing_user_name))
    if not os.path.isfile(experiment_file_path):
        raise FileNotFoundError('Experiment file {} not found'.format(experiment_file_path))
    with open(experiment_file_path, 'rb') as experiment_file:
        session = log_in(executing_user_name, executing_user_pwd)
        response = session.post(experiment_manager_upload_experiment_url, files={'data': experiment_file})
    __validate_response_status(response.status_code, 200)
    log.debug('Upload of experiment succeeded.')


def deploy_experiment(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    log.debug('Try to deploy experiment as user \'{}\'.'.format(executing_user_name))
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_deploy_experiment_url)
    __validate_response_status(response.status_code, 200)
    log.debug('Deployment of experiment succeeded.')


def delete_experiment(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    log.debug('Try to remove experiment as user \'{}\'.'.format(executing_user_name))
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.post(experiment_manager_delete_experiment_url)
    __validate_response_status(response.status_code, 200)
    log.debug('Removal of experiment succeeded.')


def get_experiment_status(executing_user_name=None, executing_user_pwd=None):
    executing_user_name, executing_user_pwd = __determine_executing_user(executing_user_name, executing_user_pwd)
    log.debug('Try to get the experiement\'s status as user \'{}\'.'.format(executing_user_name))
    session = log_in(executing_user_name, executing_user_pwd)
    response = session.get(experiment_manager_get_status_url)
    __validate_response_status(response.status_code, 200)
    log.debug('Successfully fetched experiment status: {}'.format(response.text))
    return json.loads(response.text)


def get_resource_from_id(used_resource_id, executing_user_name=None, executing_user_pwd=None):
    resources = get_experiment_status(executing_user_name, executing_user_pwd)
    for res in resources:
        if res.get('used_resource_id') == used_resource_id:
            return res.get('value').strip("'")
    raise IntegrationTestException("Resource with id %s not found" % used_resource_id)


if __name__ == '__main__':
    print(get_experiment_status())
