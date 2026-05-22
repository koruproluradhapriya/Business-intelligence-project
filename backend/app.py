import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database.mongo import get_connection_status, health_check, init_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}},
         supports_credentials=True)

    # JWT
    jwt = JWTManager(app)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired", "code": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token", "code": "invalid_token"}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Authorization token required", "code": "authorization_required"}), 401

    # Init database
    init_db(app)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.upload import upload_bp
    from routes.analytics import analytics_bp
    from routes.forecast import forecast_bp
    from routes.inventory import inventory_bp
    from routes.recommendations import recommendations_bp
    from routes.settings import settings_bp
    from routes.workspace import workspace_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(upload_bp, url_prefix='/api/upload')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(forecast_bp, url_prefix='/api/forecast')
    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(recommendations_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(workspace_bp, url_prefix='/api')

    # Health check
    @app.route('/api/health')
    def health():
        try:
            db_health = health_check()
            status = "ok" if db_health.get("ok") else "degraded"
        except Exception as exc:
            db_health = {**get_connection_status(), "ok": False, "lastError": str(exc)}
            status = "degraded"
        return jsonify({"status": status, "version": "1.0.0", "database": db_health}), (200 if status == "ok" else 503)

    # Global error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(413)
    def file_too_large(e):
        return jsonify({"error": "File too large. Max 50MB allowed."}), 413

    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)
    except OSError as e:
        if getattr(e, 'errno', None) in (48, 98):
            fallback_port = 5001
            print(f"Port {port} is in use; falling back to {fallback_port}")
            app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=fallback_port)
        else:
            raise
