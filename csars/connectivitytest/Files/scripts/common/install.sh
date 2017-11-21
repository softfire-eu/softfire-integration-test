#!/bin/bash

if [ -z $tcp_port ]; then
  >&2 echo "TCP port is not set, you have to define it in the NSD as tcp_port configuration parameter"
  exit 1
fi

if [ -z $udp_port ]; then
  >&2 echo "UDP port is not set, you have to define it in the NSD as udp_port configuration parameter"
  exit 1
fi

if [ $udp_port -eq $tcp_port ]; then
  >&2 echo "UDP and TCP port have to be different"
  exit 1
fi

sudo apt install -y nmap

if [ -z $(which nmap) ]; then
  >&2 echo "nmap was not installed successfully."
  exit 1
fi

# listen for udp and restart the connection after one second idle time.
# needed since after one client connected, no other client can connect to the udp socket without restarting.
echo "while true; do ncat -l -u -i 1 $udp_port &> /dev/null; done &"
while true; do ncat -l -u -i 1 $udp_port &> /dev/null; done &


# listen for tcp connections
echo "ncat -lk $tcp_port &"
ncat -lk $tcp_port &