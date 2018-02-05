!#/bin/bash

echo "Better to redirect output..."

sudo apt-get install -y figlet > /tmp/configure.sh

echo "first foreign key"
figlet $ubuntuclient_key_1
echo "second foreign key"
figlet $ubuntuclient_key_2
echo "foreign private ip"
echo "$ubuntuclient_softfire_internal"
echo "foreign floating ip"
echo "$ubuntuclient_softfire_internal_floatingIp"
