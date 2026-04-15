"""
API routes for the AI Tracing Prototype.

This module defines all API endpoints for the application.
"""

from datetime import datetime
from flask import jsonify, request

from app.telemetry import add_span_attributes
from app.llm_service import complete_with_ollama


def register_routes(app):
    """
    Register all routes with the Flask application.
    
    Args:
        app: Flask application instance.
    """
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint.
        
        Returns:
            JSON response with status and timestamp.
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        service_name = app.config.get('OTEL_SERVICE_NAME', 'ai-tracing-prototype')

        add_span_attributes(**{
            'health.status': 'healthy',
            'health.timestamp': timestamp,
            'service.name': service_name,
            'request.type': 'health_check',
        })

        return jsonify({
            'status': 'healthy',
            'timestamp': timestamp,
            'service': service_name
        }), 200
    
    @app.route('/', methods=['GET'])
    def index():
        """
        Root endpoint with API information.
        
        Returns:
            JSON response with available endpoints.
        """
        return jsonify({
            'service': 'AI Tracing Prototype',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'llm_complete': '/api/llm/complete (POST)',
                'rag_query': '/api/rag/query (POST)'
            }
        }), 200
    
    @app.route('/api/llm/complete', methods=['POST'])
    def llm_complete():
        """
        LLM completion endpoint.
        
        Request body:
            {
                "prompt": "Your prompt here",
                "model": "llama2" (optional),
                "max_tokens": 100 (optional),
                "temperature": 0.7 (optional)
            }
        
        Returns:
            JSON response with completion or error.
        """
        # Validate request
        if not request.is_json:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if 'prompt' not in data:
            return jsonify({
                'error': 'Missing required field',
                'message': 'Request must include "prompt" field'
            }), 400
        
        prompt = data['prompt']
        if not prompt or not isinstance(prompt, str):
            return jsonify({
                'error': 'Invalid prompt',
                'message': 'Prompt must be a non-empty string'
            }), 400
        
        # Extract optional parameters
        model = data.get('model')
        max_tokens = data.get('max_tokens')
        temperature = data.get('temperature', 0.7)
        
        # Validate temperature
        if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 1:
            return jsonify({
                'error': 'Invalid temperature',
                'message': 'Temperature must be a number between 0 and 1'
            }), 400
        
        # Add request attributes to span
        add_span_attributes(**{
            'request.type': 'llm_completion',
            'llm.prompt_length': len(prompt),
            'llm.model_requested': model or app.config.get('OLLAMA_MODEL', 'llama2'),
        })
        
        # Call LLM service
        try:
            result = complete_with_ollama(
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Check if there was an error
            if 'error' in result:
                add_span_attributes(**{
                    'error': True,
                    'error.type': result['error']
                })
                
                status_code = 503 if result['error'] == 'Ollama not available' else 500
                return jsonify(result), status_code
            
            # Add success attributes to span
            add_span_attributes(**{
                'llm.completion_length': len(result.get('completion', '')),
                'llm.total_tokens': result.get('tokens', 0),
                'llm.latency_ms': result.get('latency_ms', 0),
            })
            
            return jsonify(result), 200
        
        except Exception as e:
            add_span_attributes(**{
                'error': True,
                'error.message': str(e)
            })
            
            return jsonify({
                'error': 'Internal error',
                'message': str(e)
            }), 500
    
    # Placeholder for RAG endpoint (Phase 4)
    @app.route('/api/rag/query', methods=['POST'])
    def rag_query():
        """
        RAG query endpoint (to be implemented in Phase 4).
        
        Returns:
            JSON response indicating endpoint is not yet implemented.
        """
        return jsonify({
            'error': 'Not implemented yet',
            'message': 'This endpoint will be implemented in Phase 4'
        }), 501
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'error': 'Not found',
            'message': 'The requested endpoint does not exist'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

# Made with Bob
