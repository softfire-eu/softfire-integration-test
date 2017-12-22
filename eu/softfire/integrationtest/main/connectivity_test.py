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
wait_nfv_resource_minuties = int(get_config_value('nfv-resource', 'wait-nfv-res-min', '10'))


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

    admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)

    # create experimenter
    if create_experimenter in ['True', 'true']:
        try:
            create_user(experimenter_name, experimenter_pwd, 'experimenter', admin_session)
            log.info('Triggered the creation of a new experimenter named \'{}\'.'.format(experimenter_name))
        except Exception as e:
            log.error('Could not trigger the creation of a new experimenter named {}.'.format(experimenter_name))
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
                user_session = log_in(experimenter_name, experimenter_pwd)
                log.debug('Experimenter {} seems to be created successfully.'.format(experimenter_name))
                break
            except:
                pass
        else:
            log.error('Not able to log in as experimenter {}. Assuming the creation failed.')
            print('----------- FAILURE -----------')
            print('Experimenter {} seems not to exist after creation.'.format(experimenter_name))
            sys.exit(2)
    else:
        user_session = log_in(experimenter_name, experimenter_pwd)

    try:
        upload_experiment(experiment_file_path, session=user_session)
        log.info('Experimenter {} uploaded experiment {}.'.format(experimenter_name, experiment_file_path))
    except Exception as e:
        log.error('Experimenter {} could not upload experiment {}.'.format(experimenter_name, experiment_file_path))
        traceback.print_exc()
        failures_during_cleanup = cleanup(True, False, admin_session)
        print('----------- FAILURE -----------')
        print('Upload of experiment failed.')
        if len(failures_during_cleanup) > 0:
            print('Additionally, the following problems occurred during cleanup:')
            for problem in failures_during_cleanup:
                print(problem)
        sys.exit(2)

    try:
        deploy_experiment(user_session)
    except Exception as e:
        traceback.print_exc()
        log.error('The experiment\'s deployment failed for experimenter {}: {}'.format(experimenter_name, str(e)))
        failures_during_cleanup = cleanup(True, False, admin_session)
        print('----------- FAILURE -----------')
        print('Deployment of experiment failed.')
        if len(failures_during_cleanup) > 0:
            print('Additionally, the following problems occurred during cleanup:')
            for problem in failures_during_cleanup:
                print(problem)
        sys.exit(2)

    deployed_experiment = get_experiment_status(user_session)
    for resource in deployed_experiment:
        used_resource_id = resource.get('used_resource_id')
        # wait at most about 7 minutes for the NSR to reach active or error state
        for i in range(wait_nfv_resource_minuties * 20):
            time.sleep(3)
            resource = get_resource_from_id(used_resource_id, user_session)
            try:
                nsr = json.loads(resource)
            except Exception as e:
                log.error('Could not parse JSON of deployed resource {}: {}'.format(used_resource_id, resource))
                traceback.print_exc()
                failures_during_cleanup = cleanup(True, True, admin_session, user_session)
                print('----------- FAILURE -----------')
                print('Could not parse JSON of deployed resource {}: {}'.format(used_resource_id, resource))
                if len(failures_during_cleanup) > 0:
                    print('Additionally, the following problems occurred during cleanup:')
                    for problem in failures_during_cleanup:
                        print(problem)
                sys.exit(2)
            vnfr_list = nsr.get('vnfr')
            status_of_vnfrs = [] # contains the status of all vnfrs
            if len(vnfr_list) == 0:
                continue
            pending_vnfr = []
            for vnfr in vnfr_list:
                vnfr_name = vnfr.get('name')
                vnfr_status = vnfr.get('status')
                log.debug("Status of vnfr {} is {}".format(vnfr.get('name'), vnfr_status))
                status_of_vnfrs.append('{} is {}'.format(vnfr_name, vnfr_status))
                if vnfr_status == 'ACTIVE':
                    continue
                if vnfr_status == 'ERROR':
                    continue
                pending_vnfr.append(vnfr_name)
            if len(pending_vnfr) == 0:
                log.debug('All the VNFRs are in ACTIVE or ERROR state.')
                break
        else:
            if len(vnfr_list) == 0:
                error_message = 'Timeout: After {} minutes there were no VNFRs found in the NSR'.format(
                    wait_nfv_resource_minuties)
            else:
                error_message = 'Timeout: After {} minutes there are VNFRs not yet in ACTIVE or ERROR state: {}'.format(
                wait_nfv_resource_minuties, ', '.join(status_of_vnfrs))
            log.error(error_message)
            failures_during_cleanup = cleanup(True, True, admin_session, user_session)
            print('----------- FAILURE -----------')
            print(error_message)
            if len(failures_during_cleanup) > 0:
                print('Additionally, the following problems occurred during cleanup:')
                for problem in failures_during_cleanup:
                    print(problem)
            sys.exit(2)
    vnfr_list = nsr.get('vnfr')
    for vnfr in vnfr_list:
        vnfr_status = vnfr.get('status')
        if vnfr_status == 'ERROR':
            failed_lifecycle_events = vnfr.get('failed lifecycle events')
            for lifecycle_event in failed_lifecycle_events:
                if '0ICMP0' in lifecycle_event or '0TCP0' in lifecycle_event or '0UDP' in lifecycle_event:
                    for protocol in ['ICMP', 'UDP', 'TCP']:
                        if '0{}0'.format(protocol) in lifecycle_event and '1{}1'.format(protocol) in lifecycle_event and '2{}2'.format(protocol) in lifecycle_event:
                            _, description = lifecycle_event.split('0{}0'.format(protocol))
                            testbed, not_reachable = description.split('1{}1'.format(protocol))
                            not_reachable, _ = not_reachable.split('2{}2'.format(protocol))
                            not_reachable = not_reachable.split(' ')
                            for tb in not_reachable:
                                connection_problems.append('{} testbed could not connect to {} testbed via {}.'.format(testbed, tb, protocol))
                else:
                    additional_problems.append(
                        'VNFR {} has an ERROR lifecycle event: {}'.format(vnfr.get('name'), lifecycle_event))

    try:
        log.info("Removing experiment of {}".format(experimenter_name))
        delete_experiment(user_session)
        log.info('Removed experiment of {}.\n\n\n'.format(experimenter_name))
    except Exception as e:
        log.error('Failure during removal of experiment of {}.'.format(experimenter_name))
        traceback.print_exc()
        additional_problems.append('Removal of experiment failed.')

    if delete_experimenter in ['True', 'true']:
        try:
            admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)
            delete_user(experimenter_name, admin_session)
            log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
        except Exception as e:
            log.error('Could not remove experimenter named {}.'.format(experimenter_name))
            traceback.print_exc()

    time.sleep(1)  # otherwise the results were printed in the middle of the stack traces
    if len(connection_problems) > 0:
        print('---------- CONNECTION PROBLEMS ----------')
        for problem in connection_problems:
            print(problem)
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


def cleanup(user_created, experiment_deployed, admin_session=None, user_session=None):
    log.debug("Cleanup after a failure.")
    failures_during_cleanup = []
    if experiment_deployed:
        try:
            log.info("Removing experiment of {}".format(experimenter_name))
            delete_experiment(user_session)
            log.info('Removed experiment of {}.\n\n\n'.format(experimenter_name))
        except Exception as e:
            failures_during_cleanup.append('Failure during removal of experiment of {}.'.format(experimenter_name))
            log.error('Failure during removal of experiment of {}.'.format(experimenter_name))
            traceback.print_exc()
    if user_created:
        if delete_experimenter in ['True', 'true']:
            try:
                admin_session = log_in(exp_mngr_admin_name, exp_mngr_admin_pwd)
                delete_user(experimenter_name, admin_session)
                log.info('Successfully removed experimenter named \'{}\'.'.format(experimenter_name))
            except Exception as e:
                failures_during_cleanup.append('Could not remove experimenter named {}: {}'.format(experimenter_name, e))
                log.error('Could not remove experimenter named {}: {}'.format(experimenter_name, e))
                traceback.print_exc()
    return failures_during_cleanup
