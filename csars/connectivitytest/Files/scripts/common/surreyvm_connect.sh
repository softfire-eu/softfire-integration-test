#!/bin/bash

echo "ping -c 5 $surreyvm_softfire_internal_floatingIp"
ping -c 5 $surreyvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "Surrey" >> /home/ubuntu/pingfail
else
  echo "Surrey" >> /home/ubuntu/pingsuccess
fi

echo "ncat $surreyvm_softfire_internal_floatingIp $surreyvm_tcp_port </dev/null"
ncat $surreyvm_softfire_internal_floatingIp $surreyvm_tcp_port </dev/null
if [ $? -ne 0 ]; then
  echo "Surrey" >> /home/ubuntu/tcpfail
else
  echo "Surrey" >> /home/ubuntu/tcpsuccess
fi


i=0
echo "nc -vzu $surreyvm_softfire_internal_floatingIp $surreyvm_udp_port"
until nc -vzu $surreyvm_softfire_internal_floatingIp $surreyvm_udp_port; do
  if [ $i -gt 60 ]; then
    echo "Surrey" >> /home/ubuntu/udpfail
    exit 0
  fi
  i=$((i+1))
  sleep 1
done
echo "Surrey" >> /home/ubuntu/udpsuccess