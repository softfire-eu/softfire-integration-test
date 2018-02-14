  <img src="https://www.softfire.eu/wp-content/uploads/SoftFIRE_Logo_Fireball-300x300.png" width="120"/>

  Copyright © 2016-2018 [SoftFIRE](https://www.softfire.eu/) and [TU Berlin](http://www.av.tu-berlin.de/next_generation_networks/).
  Licensed under [Apache v2 License](http://www.apache.org/licenses/LICENSE-2.0).
  
SoftFire Integration Test
=========================

This project can be used to test the functionality of the
experiment-manager and related components.

It contains two tests, one for testing the softfire middleware and one
for testing the testbed connectivity.

Requirements
------------

Python 3.5 or higher.

Installation
------------

Git clone the repository and change into the project's directory.
Execute pip install . for installing the integration test. Afterwards
you can start it with the command softfire-integration-test. (The
connectivity test can be started with the command
softfire-testbed-connectivity-test but it is not described in more
detail here. The following information are only related to the former
test.)

Preparation
-----------

Copy the *integration-test.ini* file, which you can find in the
project's etc folder, to */etc/softfire/integration-test.ini*. Edit it
so that it fits for your testing environment. The experimenter's
*experiment* section expects the path to the experiment file which shall
be used for this experimenter in the tests and the name of the
experiment as it is defined in the csar file.

Test phases
-----------

This section describes the test phases which are executed by the
integration test.

### Preparation phase

First of all the integration test checks if the experiment files exist
and appear to be valid. If something goes wrong in this phase, the
remaining phases will not be executed and the test stops.

### Create experimenter

The configuration file has to contain *experimenter* sections which
describe the experimenters for which the integration tests are run. The
first *experimenter* section has to be named simply *experimenter*. To
add other experimenters you can add sections named *experimenter-0*,
*experimenter-1* and so on. The create experimenter phase is optional
and is only executed if the *create-user* property in the configuration
file's experimenter sections is set to *true*. It tries to create a new
experimenter in the experiment-manager whose username and password are
also defined in the configuration file in the *experimenter* section.
This is the only phase in which the *admin-username* and
*admin-password* properties from the configuration file are used.

### Upload experiment

In this phase the experiment is uploaded to the experiment-manager. The
experiment that shall be uploaded can be specified in the
*experiment-file* property in the configuration file. This action will
be executed for each experimenter and it always uses the same experiment
file.

### Deploy experiment

This phase deploys the previously uploaded experiment for each
experimenter.

### Validate experiment

In this phase the integration test checks whether all the resources
defined in the experiment are running correctly. The exact validation
procedure depends on the resource type. For example, resources of type
*NfvResource* are validated by waiting until the NSRs are in active
state and then checking if the floating IP addresses of the NSR are
reachable.

### Delete experiment

This phase removes the experiment from the experiment-manager.

### Delete experimenter

The last phase is optional and only executed if the *delete-user*
property is set in the corresponding *experimenter* section.

Adding validators for other NfvResource types
---------------------------------------------

This section describes how you can add the validation functionality for
a certain NfvResource to the integration test. Therefore you have to
create a new class in the *validators.py* module. This class has to
inherit from the AbstractValidator class and implement the *validate*
method which takes the resource, the resource ID, the experimenter's
name and the experimenter's password as arguments. In this method you
can implement the validation of the resource. If the validation is
successful, the method should simply return, otherwise it should raise
an Exception with the reason of failure as the Exception argument.

## Issue tracker

Issues and bug reports should be posted to the GitHub Issue Tracker of this project

# What is SoftFIRE?

SoftFIRE provides a set of technologies for building a federated experimental platform aimed at the construction and experimentation of services and functionalities built on top of NFV and SDN technologies.
The platform is a loose federation of already existing testbed owned and operated by distinct organizations for purposes of research and development.

SoftFIRE has three main objectives: supporting interoperability, programming and security of the federated testbed.
Supporting the programmability of the platform is then a major goal and it is the focus of the SoftFIRE’s Second Open Call.

## Licensing and distribution
Copyright © [2016-2018] SoftFIRE project

Licensed under the Apache License, Version 2.0 (the "License");

you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
