!#/bin/bash

echo "Better to redirect output..."

sudo apt-get install -y figlet > /tmp/configure.sh

echo "first foreign key"
figlet $ubuntuserver_key_1
echo "second foreign key"
figlet $ubuntuserver_key_2
echo "foreign private ip"
echo "$ubuntuserver_softfire_internal"
echo "foreign floating ip"
echo "$ubuntuserver_softfire_internal_floatingIp"
