"""
api/index.py
============
Vercel Serverless Entrypoint for Enterprise Analytics Platform
Author: Darshan K B
"""

import sys
import os

# Append project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

# Vercel looks for the WSGI application object named 'app'
if __name__ == "__main__":
    app.run()
