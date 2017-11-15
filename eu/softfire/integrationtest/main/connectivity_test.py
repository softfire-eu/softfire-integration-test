import json
import sys
import time
import traceback

from eu.softfire.integrationtest.main.experiment_manager_client import create_user, upload_experiment, \
    delete_experiment, deploy_experiment, get_resource_from_id, get_experiment_status, delete_user, \
    log_in
from eu.softfire.integrationtest.utils.utils import get_config_value
from eu.softfire.integrationtest.utils.utils import get_logger

log = get_logger(__name__)

# get config values
exp_mngr_admin_name = get_config_value('experiment-manager', 'admin-username', 'admin')
exp_mngr_admin_pwd = get_config_value('experiment-manager', 'admin-password', 'admin')
experimenter_name = get_config_value('connectivity-test', 'username')
experimenter_pwd = get_config_value('connectivity-test', 'password')
create_experimenter = get_config_value('connectivity-test', 'create-user', 'True')
delete_experimenter = get_config_value('connectivity-test', 'delete-user', 'True')
experiment_file_path = get_config_value('connectivity-test', 'experiment')
wait_nfv_resource_minuties = int(get_config_value('nfv-resource', 'wait-nfv-res-min', '7'))


def add_result(result_dict, phase, status, details):
    if phase not in result_dict:
        result_dict[phase] = {'status': status, 'details': details}
        return
    res = result_dict.get(phase)
    if status != 'OK':
        res['status'] = status
    if details != '':
        res['details'] = '{}; {}'.format(res.get('details'), details) if res.get('details') is not None and res.get(
            'details') != '' else details


def start_connectivity_test():
    log.info("Starting the SoftFIRE connectivity test.")
    connection_problems = []
    additional_problems = []

    # create experimenter
    if create_experimenter in ['True', 'true']:
        try:
            create_user(experimenter_name, experimenter_pwd, 'experimenter',
                        executing_user_name=exp_mngr_admin_name, executing_user_pwd=exp_mngr_admin_pwd)
            log.info('Triggered the creation of a new experimenter named \'{}\'.'.format(experimenter_name))
        except Exception as e:
            log.error('Could not trigger the creation of a new experimenter named {}.'.format(experimenter_pwd))
            traceback.print_exc()
            print('----------- FAILURE -----------')
            print('Could not trigger the creation of a new experimenter called {}.'.format(experimenter_name))
            sys.exit(2)

    # check if the user was created correctly
    if create_experimenter in ['True', 'true']:
        log.debug(
            'Trying to log in as user {} to check if the user was created successfully.'.format(experimenter_name))
        for i in range(0, 18):
            time.sleep(5)
            try:
                log_in(experimenter_name, experimenter_pwd)
                log.debug('Experimenter {} seems to be created successfully.'.format(experimenter_name))
                break
            except:
                pass
        else:
            log.error('Not able to log in as experimenter {}. Assuming the creation failed.')
            print('----------- FAILURE -----------')
            print('Experimenter {} seems not to exist after creation.'.format(experimenter_name))
            sys.exit(2)

    try:
        upload_experiment(experiment_file_path, experimenter_name, experimenter_pwd)
        log.info('Experimenter {} uploaded experiment {}.'.format(experimenter_name, experiment_file_path))
    except Exception as e:
        log.error('Experimenter {} could not upload experiment {}.'.format(experimenter_name, experiment_file_path))
        traceback.print_exc()
        failures_during_cleanup = cleanup(True, False)
        print('----------- FAILURE -----------')
        print('Upload of experiment failed.')
        if len(failures_during_cleanup) > 0:
            print('Additionally, the following problems occurred during cleanup:')
            for problem in failures_during_cleanup:
                print(problem)
        sys.exit(2)

    try:
        deploy_experiment(experimenter_name, experimenter_pwd)
    except Exception as e:
        traceback.print_exc()
        log.error('The experiment\'s deployment failed for experimenter {}: {}'.format(experimenter_name, str(e)))
        failures_during_cleanup = cleanup(True, False)
        print('----------- FAILURE -----------')
        print('Deployment of experiment failed.')
        if len(failures_during_cleanup) > 0:
            print('Additionally, the following problems occurred during cleanup:')
            for problem in failures_during_cleanup:
                print(problem)
        sys.exit(2)

    deployed_experiment = get_experiment_status(experimenter_name, experimenter_pwd)
    for resource in deployed_experiment:
        used_resource_id = resource.get('used_resource_id')
        # wait at most about 7 minutes for the NSR to reach active or error state
        for i in range(wait_nfv_resource_minuties * 20):
            time.sleep(3)
            resource = get_resource_from_id(used_resource_id, experimenter_name, experimenter_pwd)
            try:
                nsr = json.loads(resource)
            except Exception as e:
                log.error('Could not parse JSON of deployed resource {}: {}'.format(used_resource_id, resource))
                traceback.print_exc()
                failures_during_cleanup = cleanup(True, True)
                print('----------- FAILURE -----------')
                print('Could not parse JSON of deployed resource {}: {}'.format(used_resource_id, resource))
                if len(failures_during_cleanup) > 0:
                    print('Additionally, the following problems occurred during cleanup:')
                    for problem in failures_during_cleanup:
                        print(problem)
                sys.exit(2)
            vnfr_list = nsr.get('vnfr')
            pending_vnfr = []
            for vnfr in vnfr_list:
                vnfr_status = vnfr.get('status')
                log.debug("Status of vnfr {} is {}".format(vnfr.get('name'), vnfr_status))
                if vnfr_status == 'ACTIVE':
                    continue
                if vnfr_status == 'ERROR':
                    continue
                pending_vnfr.append(vnfr.get('name'))
            if len(pending_vnfr) == 0:
                log.debug('All the VNFRs are in ACTIVE or ERROR state.')
                break
        else:
            log.error('Timeout: After {} minutes there are VNFRs not yet in ACTIVE or ERROR state: {}'.format(
                wait_nfv_resource_minuties, ', '.join(pending_vnfr)))
            failures_during_cleanup = cleanup(True, True)
            print('----------- FAILURE -----------')
            print('Timeout: After {} minutes there are VNFRs not yet in ACTIVE or ERROR state: {}'.format(
                wait_nfv_resource_minuties, ', '.join(pending_vnfr)))
            if len(failures_during_cleanup) > 0:
                print('Additionally, the following problems occurred during cleanup:')
                for problem in failures_during_cleanup:
                    print(problem)
            sys.exit(2)

    vnfr_list = nsr.get('vnfr')
    for vnfr in vnfr_list:
        vnfr_status = vnfr.get('status')
        if vnfr_status == 'ERROR':
            lifecycle_event_history = vnfr.get('lifecycle_event_history')
            for lifecycle_event in lifecycle_event_history:
                if lifecycle_event.get('event') == 'ERROR':
                    description = lifecycle_event.get('description')
                    if '00000' in description and '11111' in description and '22222' in description:
                        _, description = description.split('00000')
                        testbed, not_reachable = description.split('11111')
                        not_reachable, _ = not_reachable.split('22222')
                        not_reachable = not_reachable.split(' ')
                        for tb in not_reachable:
                            connection_problems.append('{} testbed could not ping {} testbed.'.format(testbed, tb))
                    else:
                        additional_problems.append(
                            'VNFR {} has an ERROR lifecycle event: {}'.format(vnfr.get('name'), description))

    try:
        log.info("Removing experiment of {}".format(experimenter_name))
        delete_experiment(experimenter_name, experimenter_pwd)
        log.info('Removed experiment of {}.\n\n\n'.format(experimenter_name))
    except Exception as e:
        log.error('Failure during removal of experiment of {}.'.format(experimenter_name))
        traceback.print_exc()
        additional_problems.append('Removal of experiment failed.')

    if delete_experimenter in ['True', 'true']:
        try:
            delete_user(experimenter_name,
                        executing_user_name=exp_mngr_admin_name, executing_user_pwd=exp_mngr_admin_pwd)
            log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
        except Exception as e:
            log.error('Could not remove experimenter named {}.'.format(experimenter_pwd))
            traceback.print_exc()

    time.sleep(1)  # otherwise the results were printed in the middle of the stack traces
    if len(connection_problems) > 0:
        print('---------- CONNECTION PROBLEMS ----------')
        # TODO
        if len(additional_problems) > 0:
            print('AND there are additional problems unrelated to the testbed connectivity:')
            for problem in additional_problems:
                print(problem)
        sys.exit(1)
    else:
        print('---------------- SUCCESS ----------------')
        if len(additional_problems) > 0:
            print('BUT there are additional problems, unrelated to the testbed connectivity:')
            for problem in additional_problems:
                print(problem)
            sys.exit(2)
        else:
            sys.exit(0)


def cleanup(user_created, experiment_deployed):
    log.debug("Cleanup after a failure.")
    failures_during_cleanup = []
    if experiment_deployed:
        try:
            log.info("Removing experiment of {}".format(experimenter_name))
            delete_experiment(experimenter_name, experimenter_pwd)
            log.info('Removed experiment of {}.\n\n\n'.format(experimenter_name))
        except Exception as e:
            failures_during_cleanup.append('Failure during removal of experiment of {}.'.format(experimenter_name))
            log.error('Failure during removal of experiment of {}.'.format(experimenter_name))
            traceback.print_exc()
    if user_created:
        if delete_experimenter in ['True', 'true']:
            try:
                delete_user(experimenter_name,
                            executing_user_name=exp_mngr_admin_name, executing_user_pwd=exp_mngr_admin_pwd)
                log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
            except Exception as e:
                failures_during_cleanup.append('Could not remove experimenter named {}.'.format(experimenter_pwd))
                log.error('Could not remove experimenter named {}.'.format(experimenter_pwd))
                traceback.print_exc()
    return failures_during_cleanup
