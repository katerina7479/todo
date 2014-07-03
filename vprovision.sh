#!/usr/bin/env bash

apt-get update
apt-get install -y git
apt-get install -y python-pip
apt-get install sqlite3
cd projects
pip install -r requirements.txt
#git submodule init
#git submodule update

echo "Finished!"