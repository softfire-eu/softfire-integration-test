#!/bin/bash

echo "ping -c 5 $adsvm_softfire_internal_floatingIp"
ping -c 5 $adsvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "ADS" >> /home/ubuntu/fail
else
  echo "ADS" >> /home/ubuntu/success
fi
