from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Wallet

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password') or not data.get('username'):
        current_app.logger.warning(f"Registration attempt with missing fields - email: {bool(data.get('email') if data else False)}, password: {bool(data.get('password') if data else False)}, username: {bool(data.get('username') if data else False)}")
        return jsonify({'error': 'Missing required fields'}), 400
    
    pin = data.get('pin')
    if not pin:
        current_app.logger.warning(f"Registration attempt without PIN")
        return jsonify({'error': 'PIN is required'}), 400
    
    if not str(pin).isdigit() or len(str(pin)) != 4:
        current_app.logger.warning(f"Registration attempt with invalid PIN format: {pin}")
        return jsonify({'error': 'PIN must be exactly 4 digits'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        current_app.logger.warning(f"Registration attempt with already registered email: {data['email']}")
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        current_app.logger.warning(f"Registration attempt with already taken username: {data['username']}")
        return jsonify({'error': 'Username already taken'}), 400
    
    user = User(  # type: ignore
        email=data['email'],
        username=data['username'],
        phone=data.get('phone'),
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        university=data.get('university'),
        faculty=data.get('faculty')
    )
    user.set_password(data['password'])
    user.set_pin(pin)
    
    db.session.add(user)
    db.session.flush()
    
    wallet = Wallet(user_id=user.id)  # type: ignore
    db.session.add(wallet)
    
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        current_app.logger.warning(f"Login attempt with missing credentials - data: {bool(data)}, email: {bool(data.get('email') if data else False)}, password: {bool(data.get('password') if data else False)}")
        return jsonify({'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        current_app.logger.warning(f"Login attempt for non-existent user: {data['email']}")
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.check_password(data['password']):
        current_app.logger.warning(f"Failed login attempt with invalid password for user: {data['email']}")
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        current_app.logger.warning(f"Login attempt for deactivated account: {data['email']}")
        return jsonify({'error': 'Account is deactivated'}), 403
    
    current_app.logger.info(f"Successful login for user: {user.email}")
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_user_profile():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'email' in data and data['email'] != user.email:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 400
        user.email = data['email']
    
    if 'first_name' in data:
        user.first_name = data['first_name']
    
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    if 'phone' in data:
        user.phone = data['phone']
    
    if 'university' in data:
        user.university = data['university']
    
    if 'faculty' in data:
        user.faculty = data['faculty']
    
    db.session.commit()
    current_app.logger.info(f"Profile updated for user: {user.email}")
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user:
        current_app.logger.info(f"User logged out: {user.email}")
    
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/set-pin', methods=['POST'])
@jwt_required()
def set_pin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if user.pin_hash is not None:
        current_app.logger.warning(f"Attempt to use deprecated set-pin endpoint for existing PIN: {user.email}")
        return jsonify({
            'error': 'PIN already set. Use /auth/change-pin to update your PIN.',
            'requires_password': True
        }), 403
    
    data = request.get_json()
    pin = data.get('pin')
    
    if not pin or len(str(pin)) != 4 or not str(pin).isdigit():
        return jsonify({'error': 'PIN must be exactly 4 digits'}), 400
    
    user.set_pin(pin)
    db.session.commit()
    
    current_app.logger.info(f"Initial PIN set for user: {user.email}")
    return jsonify({'message': 'PIN set successfully'}), 200

@auth_bp.route('/verify-pin', methods=['POST'])
@jwt_required()
def verify_pin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    pin = data.get('pin')
    
    if user.check_pin(pin):
        return jsonify({'valid': True}), 200
    else:
        return jsonify({'valid': False}), 400

@auth_bp.route('/change-pin', methods=['POST'])
@jwt_required()
def change_pin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('password')
    new_pin = data.get('new_pin')
    confirm_pin = data.get('confirm_pin')
    
    if not current_password:
        return jsonify({'error': 'Current password is required'}), 400
    
    if not user.check_password(current_password):
        current_app.logger.warning(f"Failed PIN change attempt with invalid password for user: {user.email}")
        return jsonify({'error': 'Invalid password'}), 401
    
    if not new_pin or len(str(new_pin)) != 4 or not str(new_pin).isdigit():
        return jsonify({'error': 'New PIN must be exactly 4 digits'}), 400
    
    if new_pin != confirm_pin:
        return jsonify({'error': 'PINs do not match'}), 400
    
    if new_pin == '1234':
        return jsonify({'error': 'Please choose a PIN other than the default 1234', 'is_default_pin': True}), 400
    
    user.set_pin(new_pin)
    db.session.commit()
    
    current_app.logger.info(f"PIN changed successfully for user: {user.email}")
    return jsonify({'message': 'PIN changed successfully'}), 200

@auth_bp.route('/check-default-pin', methods=['GET'])
@jwt_required()
def check_default_pin():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    has_default_pin = user.check_pin('1234')
    has_pin = user.pin_hash is not None
    
    return jsonify({
        'has_pin': has_pin,
        'is_default_pin': has_default_pin
    }), 200
