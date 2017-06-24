import time

from eu.softfire.integrationtest.utils.utils import get_logger
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.main.experiment_manager_client import create_user, upload_experiment, \
    delete_experiment, deploy_experiment, get_status

log = get_logger(__name__)


class IntegrationTest():

    def __init__(self):
        pass

    def start(self):
        log.info("Starting the SoftFIRE integration tests.")
        # get config values
        exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
        exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
        experimenter_name = get_config_value('experimenter', 'username')
        experimenter_password = get_config_value('experimenter', 'password')
        experiment_file_path = get_config_value('general', 'experiment-file')

        if get_config_value('general', 'create-user', 'True') in ['True', 'true']:
            # create a new experimenter
            create_user(experimenter_name, experimenter_password, 'experimenter', executing_user_name=exp_mngr_admin_name, executing_user_pwd=exp_mngr_admin_pwd)
        # upload experiment
        upload_experiment(experiment_file_path)
        # deploy experiment
        deploy_experiment()
        # TODO validate deployment
        # delete experiment
        delete_experiment()


