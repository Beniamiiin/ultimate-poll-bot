from flask import Flask

from resources.routes import initialize_routes

app = Flask(__name__)
initialize_routes(app)
