import os
import sys

# Ensure root directory is on Python path so backend modules resolve
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app

# Vercel serverless function expects the ASGI app
# 'app' is the FastAPI instance from app.py
