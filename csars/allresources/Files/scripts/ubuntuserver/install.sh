#!/bin/bash

echo "Use simple debug messages to understand where the issues could be"
echo "installing!!!"
echo "Avoid long outputs! so redirect the output to a file that you can later check, for instance:"
sudo apt-get update > /tmp/install.log
echo "apt update worked!"
sudo apt-get install -y cowsay >> /tmp/install.log

echo "check the env before running special commands"
env
echo "like this one..."
/usr/games/cowsay -f tux "install successfull"
