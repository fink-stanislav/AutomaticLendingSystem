
from app import app

from flask import render_template

@app.route('/')
@app.route('/dashboard')
def render_dashboard():
    """
    Renders Dashboard page
    """
    return render_template('dashboard.html', title='ALS Dahboard')

@app.route('/current_loans_data')
def get_current_loans_data():
    """
    Returns current loans: active and pending
    """
    pass

@app.route('/balance_data')
def get_balance_data():
    """
    Returns current balance and data for building balance changing graph
    """
    pass