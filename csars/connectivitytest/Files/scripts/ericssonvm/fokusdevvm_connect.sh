#!/bin/bash

echo "ping -c 5 $fokusdevvm_softfire_internal_floatingIp"
ping -c 5 $fokusdevvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "FOKUS-dev" >> /home/ubuntu/fail
else
  echo "FOKUS-dev" >> /home/ubuntu/success
fi
