#!/bin/bash

echo "ping -c 5 $adsvm_softfire_internal_floatingIp"
ping -c 5 $adsvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "ADS" >> /home/ubuntu/pingfail
else
  echo "ADS" >> /home/ubuntu/pingsuccess
fi

echo "ncat $adsvm_softfire_internal_floatingIp $adsvm_tcp_port </dev/null"
ncat $adsvm_softfire_internal_floatingIp $adsvm_tcp_port </dev/null
if [ $? -ne 0 ]; then
  echo "ADS" >> /home/ubuntu/tcpfail
else
  echo "ADS" >> /home/ubuntu/tcpsuccess
fi


i=0
echo "nc -vzu $adsvm_softfire_internal_floatingIp $adsvm_udp_port"
until nc -vzu $adsvm_softfire_internal_floatingIp $adsvm_udp_port; do
  if [ $i -gt 60 ]; then
    echo "ADS" >> /home/ubuntu/udpfail
    exit 0
  fi
  i=$((i+1))
  sleep 1
done
echo "ADS" >> /home/ubuntu/udpsuccess