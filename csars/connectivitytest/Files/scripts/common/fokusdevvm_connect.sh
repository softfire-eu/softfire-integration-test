#!/bin/bash

echo "ping -c 5 $fokusdevvm_softfire_internal_floatingIp"
ping -c 5 $fokusdevvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "FOKUS-dev" >> /home/ubuntu/pingfail
else
  echo "FOKUS-dev" >> /home/ubuntu/pingsuccess
fi

echo "ncat $fokusdevvm_softfire_internal_floatingIp $fokusdevvm_tcp_port </dev/null"
ncat $fokusdevvm_softfire_internal_floatingIp $fokusdevvm_tcp_port </dev/null
if [ $? -ne 0 ]; then
  echo "FOKUS-dev" >> /home/ubuntu/tcpfail
else
  echo "FOKUS-dev" >> /home/ubuntu/tcpsuccess
fi


i=0
echo "nc -vzu $fokusdevvm_softfire_internal_floatingIp $fokusdevvm_udp_port"
until nc -vzu $fokusdevvm_softfire_internal_floatingIp $fokusdevvm_udp_port; do
  if [ $i -gt 60 ]; then
    echo "FOKUS-dev" >> /home/ubuntu/udpfail
    exit 0
  fi
  i=$((i+1))
  sleep 1
done
echo "FOKUS-dev" >> /home/ubuntu/udpsuccess