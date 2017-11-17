import json
import os
import traceback

import requests

from eu.softfire.integrationtest.utils.exceptions import IntegrationTestException
from eu.softfire.integrationtest.utils.utils import get_config_value, get_logger

experiment_manager_ip = get_config_value('experiment-manager', 'ip', 'localhost')
experiment_manager_port = get_config_value('experiment-manager', 'port', '5080')
experiment_manager_login_url = 'http://{}:{}/login'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_create_user_url = 'http://{}:{}/create_user'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_delete_user_url = 'http://{}:{}/delete_user'.format(experiment_manager_ip, experiment_manager_port)
experiment_manager_upload_experiment_url = 'http://{}:{}/reserve_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
experiment_manager_deploy_experiment_url = 'http://{}:{}/provide_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
experiment_manager_delete_experiment_url = 'http://{}:{}/release_resources'.format(experiment_manager_ip,
                                                                                   experiment_manager_port)
experiment_manager_get_status_url = 'http://{}:{}/get_status'.format(experiment_manager_ip, experiment_manager_port)

log = get_logger(__name__)


def __validate_response_status(response, expected_status, error_message=None):
    if not isinstance(expected_status, list):
        expected_status = [expected_status]

    if response.status_code not in expected_status:
        content = response.content
        try:
            content = content.decode('UTF-8')
        except:
            pass
        error_message = 'HTTP response status code was {}, but expected was {}'.format(response.status_code,
                                                                                        expected_status) or error_message
        log.error('HTTP response status code was {}, but expected was {}: {}'.format(response.status_code,
                                                                                        expected_status, content))
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
        __validate_response_status(log_in_response, [200],
                                   'experiment-manager log in failed for user {}. HTTP response status code was {}, but expected was {}.'.format(
                                       username, log_in_response, [200]))
        response_text_dict = json.loads(log_in_response.text)
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
    if (not response_text_dict.get('ok')) or response_text_dict.get('ok') == False:
        error_message = 'experiment-manager log in failed: {}'.format(response_text_dict.get('msg'))
        log.error(error_message)
        raise Exception(error_message)
    log.debug('Log in succeeded for user {}.'.format(username))
    return session


def create_user(new_user_name, new_user_pwd, new_user_role, session):
    log.debug('Try to create a new user named \'{}\'.'.format(new_user_name))
    response = session.post(experiment_manager_create_user_url,
                            data={'username': new_user_name, 'password': new_user_pwd, 'role': new_user_role})
    __validate_response_status(response, [200, 202])
    log.debug('Triggered the creation of a new user named \'{}\'.'.format(new_user_name))


def delete_user(user_name_to_delete, session):
    log.debug('Try to delete the user named \'{}\'.'.format(user_name_to_delete))
    response = session.post(experiment_manager_delete_user_url,
                            data={'username': user_name_to_delete})
    __validate_response_status(response, 200)
    log.debug('Creation of a new user named \'{}\' succeeded.'.format(user_name_to_delete))


def upload_experiment(experiment_file_path, session):
    log.debug('Try to upload experiment.')
    if not os.path.isfile(experiment_file_path):
        raise FileNotFoundError('Experiment file {} not found'.format(experiment_file_path))
    with open(experiment_file_path, 'rb') as experiment_file:
        response = session.post(experiment_manager_upload_experiment_url, files={'data': experiment_file})
    __validate_response_status(response, 200)
    log.debug('Upload of experiment succeeded.')


def deploy_experiment(session, queue=None):
    try:
        log.debug('Try to deploy experiment.')
        response = session.post(experiment_manager_deploy_experiment_url)
        __validate_response_status(response, 200)
        log.debug('Deployment of experiment succeeded.')
        if queue is not None:
            queue.put(None)
    except Exception as e:
        if queue is not None:
            traceback.print_exc()
            queue.put(e)
        else:
            raise e



def delete_experiment(session):
    log.debug('Try to remove experiment.')
    response = session.post(experiment_manager_delete_experiment_url)
    __validate_response_status(response, 200)
    log.debug('Removal of experiment succeeded.')


def get_experiment_status(session):
    log.debug('Try to get the experiement\'s status.')
    response = session.get(experiment_manager_get_status_url)
    __validate_response_status(response, 200)
    # log.debug('Successfully fetched experiment status: {}'.format(response.text))
    return json.loads(response.text)


def get_resource_from_id(used_resource_id, session):
    resources = get_experiment_status(session)
    for res in resources:
        if res.get('used_resource_id') == used_resource_id:
            return res.get('value').strip("'")
    raise IntegrationTestException("Resource with id %s not found" % used_resource_id)


