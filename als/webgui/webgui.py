"""
Entry point module for Flask application
"""
from app import app

from als.util import custom_config as cc

if __name__ == '__main__':
    port = cc.get_webgui_port()
    debug_mode = cc.get_webgui_debug_mode()
    app.run(debug=debug_mode, port=port)
