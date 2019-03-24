#!/bin/bash

echo "Starting Server"

cd /ie-serving-py
source /ie-serving-py/.venv/bin/activate

/ie-serving-py/start_server.sh ie_serving \
config --config_path \
/opt/ml/config.json \
--port 9001 &

echo "starting api"
cd /var/sugar

python3 api.py
