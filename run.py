#!/usr/bin/env python3
"""
Application entry point for the AI Tracing Prototype.

This script starts the Flask development server.
"""

from app import create_app
from app.config import Config

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting AI Tracing Prototype")
    print("="*50)
    
    # Run the Flask development server
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.FLASK_DEBUG
    )

# Made with Bob
