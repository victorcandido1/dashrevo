"""
Manifest Routes
Handles passenger manifest processing
"""
from flask import Blueprint, jsonify, request

manifesto_bp = Blueprint('manifesto', __name__)


@manifesto_bp.route('/overview')
def get_overview():
    """Get manifest overview"""
    return jsonify({'message': 'Manifest endpoint - to be implemented'})
