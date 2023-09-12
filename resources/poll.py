import traceback
from sqlalchemy import select
from flask_restful import Resource, abort, marshal_with, fields

from pollbot.db import get_session
from pollbot.models import Poll
from resources.helpers.option import PollOption


vote_model = {
    'yes': fields.Integer,
    'no': fields.Integer,
    'acknowledge': fields.Integer
}

poll_model = {
    'id': fields.Integer,
    'votes': fields.Nested(vote_model)
}


class PollApi(Resource):
    @marshal_with(poll_model)
    def get(self, poll_id: int):
        session = get_session()

        stmt = select(Poll).where(Poll.id == poll_id)
        poll = session.scalar(stmt)

        if poll is None:
            abort(404, message='Not found')

        yesOptionsCount = 0
        noOptionsCount = 0
        acknowledgeOptionsCount = 0

        for vote in poll.votes:
            match vote.option.name:
                case PollOption.Yes:
                    yesOptionsCount += 1
                case PollOption.No:
                    noOptionsCount += 1
                case PollOption.Acknowledge:
                    acknowledgeOptionsCount += 1

        return {
            'id': poll.id,
            'votes': {
                'yes': yesOptionsCount,
                'no': noOptionsCount,
                'acknowledge': acknowledgeOptionsCount,
            }
        }, 200
