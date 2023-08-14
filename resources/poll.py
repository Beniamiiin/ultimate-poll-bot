from datetime import datetime, timedelta

from flask_restful import Resource
from sqlalchemy import select

from pollbot.db import get_session
from pollbot.enums import ReferenceType, PollType
from pollbot.helper.stats import increase_stat, increase_user_stat
from pollbot.models import Poll, User, Reference
from pollbot.poll.option import add_single_option


class PollApi(Resource):
    def post(self):
        session = get_session()

        stmt = select(User).where(User.id == 83758704)

        user = session.scalar(stmt)

        poll = Poll.create(user, session)
        poll.name = "Poll name from api"
        poll.description = "Poll description from api"
        poll.poll_type = PollType.single_vote.name
        poll.anonymous = True
        poll.results_visible = True
        poll.due_date = datetime.today() + timedelta(days=14)
        poll.created = True

        add_single_option(session, poll, 'Yes', False)
        add_single_option(session, poll, 'No', False)
        add_single_option(session, poll, 'Acknowledge', False)

        user.expected_input = None
        user.current_poll = None

        reference = Reference(
            poll, ReferenceType.admin.name, user=user, message_id=1
        )
        session.add(reference)
        session.commit()

        increase_stat(session, "created_polls")
        increase_user_stat(session, user, "created_polls")

        return 'Ok', 200
