#!/bin/bash

echo "ping -c 5 $fokusvm_softfire_internal_floatingIp"
ping -c 5 $fokusvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "FOKUS" >> /home/ubuntu/pingfail
else
  echo "FOKUS" >> /home/ubuntu/pingsuccess
fi

echo "ncat $fokusvm_softfire_internal_floatingIp $fokusvm_tcp_port </dev/null"
ncat $fokusvm_softfire_internal_floatingIp $fokusvm_tcp_port </dev/null
if [ $? -ne 0 ]; then
  echo "FOKUS" >> /home/ubuntu/tcpfail
else
  echo "FOKUS" >> /home/ubuntu/tcpsuccess
fi


i=0
echo "nc -vzu $fokusvm_softfire_internal_floatingIp $fokusvm_udp_port"
until nc -vzu $fokusvm_softfire_internal_floatingIp $fokusvm_udp_port; do
  if [ $i -gt 60 ]; then
    echo "FOKUS" >> /home/ubuntu/udpfail
    exit 0
  fi
  i=$((i+1))
  sleep 1
done
echo "FOKUS" >> /home/ubuntu/udpsuccess