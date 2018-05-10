
from app import app

from flask import render_template

@app.route('/statistics')
def render_statistics():
    """
    Renders statistics page
    """
    return render_template('statistics.html', title='ALS Statistics')

@app.route('/statistics_data')
def get_statistics_data():
    """
    Returns data for building indicators graphs
    """
    pass
