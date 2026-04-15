"""
Flask application factory for the AI Tracing Prototype.

This module initializes the Flask application and sets up routes.
"""

from flask import Flask
from app.config import Config
from app.telemetry import initialize_telemetry


def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance.
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Validate configuration
    Config.validate()
    
    # Display configuration
    if Config.FLASK_DEBUG:
        Config.display()
    
    # Initialize telemetry
    initialize_telemetry(app, Config)

    # Register routes
    from app.routes import register_routes
    register_routes(app)
    
    return app

# Made with Bob
