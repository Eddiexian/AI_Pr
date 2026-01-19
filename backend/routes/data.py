from flask import Blueprint, request, jsonify, current_app
from services.data_provider import get_data_provider

bp = Blueprint('data', __name__, url_prefix='/api/data')

@bp.route('/wip', methods=['POST'])
def get_wip_data():
    """
    Expects JSON: { "binCodes": ["A-01", "B-02"] }
    Returns WIP data for those bins.
    """
    data = request.get_json()
    bin_codes = data.get('binCodes', [])
    
    if not bin_codes:
        return jsonify({})
        
    provider = get_data_provider(current_app.config)
    results = provider.get_wip_by_layout_bins(bin_codes)
    
    return jsonify(results)
@bp.route('/counts', methods=['POST'])
def get_bin_counts():
    """
    Expects JSON: { "binCodes": ["A-01", "B-02"] }
    Returns summary counts (e.g. cassette count) for those bins.
    """
    data = request.get_json()
    bin_codes = data.get('binCodes', [])
    if not bin_codes:
        return jsonify({})
    
    provider = get_data_provider(current_app.config)
    results = provider.get_counts_by_layout_bins(bin_codes)
    return jsonify(results)
