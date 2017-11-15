#!/bin/bash

if [ -f /home/ubuntu/fail ]; then
  while read LINE; do message="$message $LINE"; done < /home/ubuntu/fail
  >&2 echo "00000Ericsson11111${message}22222" # 00000 ... 11111 ... 22222 marks this error message as important for the connectivity test
  exit 1
fi
