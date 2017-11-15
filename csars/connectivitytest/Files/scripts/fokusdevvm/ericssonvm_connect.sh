#!/bin/bash

echo "ping -c 5 $ericssonvm_softfire_internal_floatingIp"
ping -c 5 $ericssonvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "Ericsson" >> /home/ubuntu/fail
else
  echo "Ericsson" >> /home/ubuntu/success
fi
