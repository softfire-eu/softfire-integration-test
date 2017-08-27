=========================
SoftFire Integration Test
=========================
This project can be used to test the functionality of the
experiment-manager and related components.

Requirements
============
Python 3.5 or higher.

Installation
============
Git clone the repository and change into the project's directory. Execute :code:`pip install .` for installing the integration test. Afterwards you can start it with the command :code:`softfire-integration-test`.


Preparation
===========
Copy the *integration-test.ini* file, which you can find in the project's etc folder, to */etc/softfire/integration-test.ini*.
Edit it so that it fits for your testing environment.


Test phases
============
This section describes the test phases which are executed by the integration test.

Preparation phase
-----------------
First of all the integration test checks if the experiment file exists and scans it for the resources it uses.
If something goes wrong in this phase, the remaining phases will not be executed and the test stops.


Create experimenter
-------------------
The configuration file has to contain *experimenter* sections which describe the experimenters for which the integration tests are run.
The first *experimenter* section has to be named simply *experimenter*.
To add other experimenters you can add sections named *experimenter-0*, *experimenter-1* and so on.
The create experimenter phase is optional and is only executed if the *create-user* property in the configuration file's experimenter sections is set to *true*.
It tries to create a new experimenter in the experiment-manager whose username and password are also defined in the configuration file in the *experimenter* section. This is the only phase in which the *admin-username* and *admin-password* properties from the configuration file are used.


Upload experiment
-----------------
In this phase the experiment is uploaded to the experiment-manager. The experiment that shall be uploaded can be specified in the *experiment-file* property in the configuration file. This action will be executed for each experimenter and it always uses the same experiment file.


Deploy experiment
-----------------
This phase deploys the previously uploaded experiment for each experimenter.

Validate experiment
-------------------
In this phase the integration test checks whether all the resources defined in the experiment are running correctly.
The exact validation procedure depends on the resource type.
For example, resources of type *NfvResource* are validated by waiting until the NSRs are in active state and then checking if the floating IP addresses of the NSR are reachable.

Delete experiment
-----------------
This phase removes the experiment from the experiment-manager.

Delete experimenter
-------------------
The last phase is optional and only executed if the *delete-user* property is set in the corresponding *experimenter* section.


Adding validators for other NfvResource types
=============================================
This section describes how you can add the validation functionality for a certain NfvResource to the integration test.
Therefore you have to create a new class in the *validators.py* module. This class has to inherit from the AbstractValidator class and implement the *validate* method which takes the resource, the resource ID, the experimenter's name and the experimenter's password as arguments.
In this method you can implement the validation of the resource. If the validation is successful, the method should simply return, otherwise it should raise an Exception with the reason of failure as the Exception argument.