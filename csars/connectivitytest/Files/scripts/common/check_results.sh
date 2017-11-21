#!/bin/bash

failed=false


case $(hostname) in
  ericssonvm-*)
      MYSELF="Ericsson"
    ;;
  fokusdevvm-*)
      MYSELF="FOKUS-dev"
    ;;
  ericssonvm-*)
      MYSELF="Ericsson"
    ;;
  fokusvm-*)
      MYSELF="FOKUS"
    ;;
  surreyvm-*)
      MYSELF="Surrey"
    ;;
  *)
      MYSELF=$(hostname)
    ;;
esac



if [ -f /home/ubuntu/pingfail ]; then
  not_reached=""
  while read LINE; do
    if [ -z "$not_reached" ]; then
      not_reached=$LINE
    else
      not_reached="$not_reached $LINE"
    fi
  done < /home/ubuntu/pingfail
  >&2 echo "0ICMP0${MYSELF}1ICMP1${not_reached}2ICMP2" # 0ICMP0 ... 1ICMP1 ... 2ICMP2 marks this error message as icmp result for the connectivity test and acts as a separator
  failed=true
fi

if [ -f /home/ubuntu/udpfail ]; then
  not_reached=""
  while read LINE; do
    if [ -z "$not_reached" ]; then
      not_reached=$LINE
    else
      not_reached="$not_reached $LINE"
    fi
  done < /home/ubuntu/udpfail
  >&2 echo "0UDP0${MYSELF}1UDP1${not_reached}2UDP2" # 0UDP0 ... 1UDP1 ... 2UDP2 marks this error message as udp result for the connectivity test and acts as a separator
  failed=true
fi

if [ -f /home/ubuntu/tcpfail ]; then
  not_reached=""
  while read LINE; do
    if [ -z "$not_reached" ]; then
      not_reached=$LINE
    else
      not_reached="$not_reached $LINE"
    fi
  done < /home/ubuntu/tcpfail
  >&2 echo "0TCP0${MYSELF}1TCP1${not_reached}2TCP2" # 0TCP0 ... 1TCP1 ... 2TCP2 marks this error message as tcp result for the connectivity test and acts as a separator
  failed=true
fi

if $failed; then
  exit 1
fi
