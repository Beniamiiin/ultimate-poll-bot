from flask import request
from flask_restful import Resource, abort, marshal_with, fields

from pollbot.db import get_session
from pollbot.models import Poll
from resources.helpers.option import PollOption


vote_model = {
    'user_id': fields.Integer,
    'option': fields.String
}


class VoteListApi(Resource):
    @marshal_with(vote_model)
    def get(self):
        session = get_session()
        poll_id = request.args.get('poll_id')

        poll = session.query(Poll).where(Poll.id == poll_id)

        if poll is None:
            abort(404, message='Not found')

        votes = []

        for vote in poll.votes:
            vote_json = {
                'user_id': vote.user.id,
            }

            match vote.option.name:
                case PollOption.Yes:
                    vote_json['option'] = 'yes'
                case PollOption.No:
                    vote_json['option'] = 'no'
                case PollOption.Acknowledge:
                    vote_json['option'] = 'acknowledged'

            votes.append(vote_json)

        return votes, 200
