
from app import app

@app.route('/')
def get_time():
    return 'hello world'
