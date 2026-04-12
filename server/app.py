"""
OpenEnv server entry point.
Exposes the Flask app for multi-mode deployment.
"""
from api_server import app, main

if __name__ == "__main__":
    main()
