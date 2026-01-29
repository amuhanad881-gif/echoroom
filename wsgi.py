#!/usr/bin/env python3
"""
WSGI entry point for Squad Talk
Use this file for production deployment
"""

from app import app, socketio

if __name__ == "__main__":
    # Production configuration
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )
