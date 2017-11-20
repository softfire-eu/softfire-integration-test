#!/bin/bash

echo "ping -c 5 $ericssonvm_softfire_internal_floatingIp"
ping -c 5 $ericssonvm_softfire_internal_floatingIp
if [ $? -ne 0 ]; then
  echo "Ericsson" >> /home/ubuntu/pingfail
else
  echo "Ericsson" >> /home/ubuntu/pingsuccess
fi

echo "ncat $ericssonvm_softfire_internal_floatingIp $ericssonvm_tcp_port </dev/null"
ncat $ericssonvm_softfire_internal_floatingIp $ericssonvm_tcp_port </dev/null
if [ $? -ne 0 ]; then
  echo "Ericsson" >> /home/ubuntu/tcpfail
else
  echo "Ericsson" >> /home/ubuntu/tcpsuccess
fi


i=0
echo "nc -vzu $ericssonvm_softfire_internal_floatingIp $ericssonvm_udp_port"
until nc -vzu $ericssonvm_softfire_internal_floatingIp $ericssonvm_udp_port; do
  if [ $i -gt 60 ]; then
    echo "Ericsson" >> /home/ubuntu/udpfail
    exit 0
  fi
  i=$((i+1))
  sleep 1
done
echo "Ericsson" >> /home/ubuntu/udpsuccess