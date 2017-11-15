#!/bin/bash

echo "ping -c 5 $surreyvm_softfire_internal_floatingIp"
ping -c 5 $surreyvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "Surrey" >> /home/ubuntu/fail
else
  echo "Surrey" >> /home/ubuntu/success
fi
