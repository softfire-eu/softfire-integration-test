#!/bin/bash

echo "ping -c 5 $fokusvm_softfire_internal_floatingIp"
ping -c 5 $fokusvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "FOKUS" >> /home/ubuntu/fail
else
  echo "FOKUS" >> /home/ubuntu/success
fi
