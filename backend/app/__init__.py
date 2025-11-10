from flask import Flask
from config import config
from app.extensions import db, jwt, socketio, cors, migrate

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    socketio.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        from app import models
    
    from app.blueprints.auth import auth_bp
    from app.blueprints.wallet import wallet_bp
    from app.blueprints.transactions import transactions_bp
    from app.blueprints.cards import cards_bp
    from app.blueprints.savings import savings_bp
    from app.blueprints.marketplace import marketplace_bp
    from app.blueprints.loans import loans_bp
    from app.blueprints.subscriptions import subscriptions_bp
    from app.blueprints.isic import isic_bp
    from app.blueprints.isic_upload import isic_upload_bp
    from app.blueprints.expected_payments import expected_payments_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(cards_bp, url_prefix='/api/cards')
    app.register_blueprint(savings_bp, url_prefix='/api/savings')
    app.register_blueprint(marketplace_bp, url_prefix='/api/marketplace')
    app.register_blueprint(loans_bp, url_prefix='/api/loans')
    app.register_blueprint(subscriptions_bp, url_prefix='/api/subscriptions')
    app.register_blueprint(isic_bp, url_prefix='/api/isic')
    app.register_blueprint(isic_upload_bp)
    app.register_blueprint(expected_payments_bp, url_prefix='/api/expected-payments')
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok', 'message': 'UniPay API is running'}
    
    return app
