#!/bin/bash

# This script sets up a Python virtual environment and installs required packages.

# Define the environment name
env_name="buoy_env"

# Create a virtual environment
python3 -m venv $env_name

# Activate the virtual environment
source $env_name/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required Python packages
pip install requests Pillow numpy opencv-python

# Optional: Install additional packages for OpenCV features
pip install opencv-contrib-python

# Print completion message
echo "Setup complete. To activate the environment, run: source $env_name/bin/activate"
