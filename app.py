from flask import Flask
from routes import searchsalarios_bp, search_bp, cfe_bp
import os

app = Flask(__name__)
app.register_blueprint(searchsalarios_bp)
app.register_blueprint(search_bp)
app.register_blueprint(cfe_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
