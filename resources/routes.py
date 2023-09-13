from flask_restful import Api
from resources.health_check import HealthCheckApi
from resources.poll_list import PollListApi
from resources.vote_list import VoteListApi


def initialize_routes(app):
    api = Api(app)
    api.add_resource(HealthCheckApi, '/healthcheck')
    api.add_resource(PollListApi, '/poll')
    api.add_resource(VoteListApi, '/vote')
