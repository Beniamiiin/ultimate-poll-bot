from flask_restful import Api
from resources.health_check import HealthCheckApi
from resources.poll import PollApi


def initialize_routes(app):
    api = Api(app)
    api.add_resource(HealthCheckApi, '/healthcheck')
    api.add_resource(PollApi, '/poll')
