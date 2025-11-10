from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Transaction
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('', methods=['GET'])
@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    transaction_type = request.args.get('type')
    
    query = Transaction.query.filter_by(user_id=user_id)
    
    if transaction_type:
        query = query.filter_by(transaction_type=transaction_type)
    
    query = query.order_by(Transaction.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    transactions = [t.to_dict() for t in pagination.items]
    
    return jsonify({
        'transactions': transactions,
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages,
        'per_page': per_page
    }), 200

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    user_id = int(get_jwt_identity())
    
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=user_id).first()
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    return jsonify({'transaction': transaction.to_dict()}), 200

@transactions_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_transaction_stats():
    user_id = int(get_jwt_identity())
    
    from sqlalchemy import func
    from app.extensions import db
    from app.models import Wallet
    
    # Calculate total income: topup, income, refund, transfer_received, loan_repayment_received, loan_received, savings_withdrawal, sale, budget_withdrawal
    total_income = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type.in_([
            'topup', 'income', 'refund', 'transfer_received', 
            'loan_repayment_received', 'loan_received', 'savings_withdrawal',
            'sale', 'budget_withdrawal'
        ])
    ).scalar() or 0
    
    # Calculate total expenses: payment, purchase, transfer_sent, card_payment, loan_disbursement, loan_repayment, savings_deposit, budget_allocation, budget_expense
    total_expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type.in_([
            'payment', 'purchase', 'transfer_sent', 'card_payment', 
            'loan_disbursement', 'loan_repayment', 'savings_deposit',
            'budget_allocation', 'budget_expense'
        ])
    ).scalar() or 0
    
    # Get current wallet balance
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    current_balance = float(wallet.balance) if wallet else 0.0
    
    # Get transaction count
    transaction_count = Transaction.query.filter_by(user_id=user_id).count()
    
    recent_transactions = Transaction.query.filter_by(user_id=user_id).order_by(
        Transaction.created_at.desc()
    ).limit(5).all()
    
    return jsonify({
        'total_income': float(total_income),
        'total_expenses': float(total_expenses),
        'current_balance': current_balance,
        'transaction_count': transaction_count,
        'recent_transactions': [t.to_dict() for t in recent_transactions]
    }), 200
