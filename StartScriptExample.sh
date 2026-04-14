#!/usr/bin/bash

# This is an example for a script that activates the virtual environment and launches the app.
# Replace the project directory with the one you use.

project_directory="/foo/bar/BMA-Simulator"

cd  $project_directory || (echo "Starting bma_control failed: Unable to open specified project directory $project_directory"; exit)
source .venv/bin/activate
python ./bma_control
cd ~ || exit
