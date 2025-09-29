#!/usr/bin/env python3
"""
Simple script to run the backend from the backend folder
"""
import subprocess
import sys
import os

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)

# Run uvicorn
subprocess.run([sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'])
