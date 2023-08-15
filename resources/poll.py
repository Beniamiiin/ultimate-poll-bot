import logging
import traceback
from datetime import datetime, timedelta

import telegram
from flask_restful import Resource
from sqlalchemy import select

from pollbot.config import config
from pollbot.db import get_session
from pollbot.display.poll.compilation import get_poll_text_and_vote_keyboard
from pollbot.enums import ReferenceType, PollType
from pollbot.models import Poll, User, Reference
from pollbot.poll.option import add_option


class PollApi(Resource):
    def post(self):
        session = get_session()

        stmt = select(User).where(User.id == 83758704)

        user = session.scalar(stmt)

        poll = Poll(user)
        poll.name = "Poll name from api"
        poll.description = "Poll description from api"
        poll.locale = user.locale
        poll.poll_type = PollType.single_vote.name
        poll.number_of_votes = 0
        poll.anonymous = True
        poll.results_visible = False
        poll.set_due_date(datetime.today() + timedelta(days=14))
        poll.allow_new_options = False
        poll.allow_sharing = False
        poll.show_percentage = True
        poll.show_option_votes = True
        poll.european_date_format = user.european_date_format
        poll.permanently_summarized = False
        poll.compact_buttons = False
        poll.summarize = False
        poll.created = True
        session.add(poll)

        for option_to_add in ['Yes', 'No', 'Acknowledge']:
            option = add_option(poll, option_to_add, [], False)
            if option is None:
                continue

            session.add(option)

        user.expected_input = None
        user.current_poll = None

        session.flush()

        reference = Reference(poll, ReferenceType.admin.name, user=user, message_id=1)
        session.add(reference)
        session.commit()

        text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)

        try:
            logging.basicConfig(
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
            )

            telegram.Bot(token=config['telegram']['api_key']).send_message(
                text=text,
                chat_id=-1001800658028,
                reply_markup=keyboard,
                parse_mode="markdown",
                disable_web_page_preview=True,
            )
        except:
            traceback.print_exc()

            session.delete(poll)
            session.commit()

        return 'Ok', 200
