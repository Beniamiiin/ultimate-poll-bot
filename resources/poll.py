import traceback
from datetime import datetime, timedelta

import telegram
from dateutil import parser
from flask import request
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
        request_body = request.get_json()

        api_config = config['api']

        stmt = select(User).where(User.username == api_config['admin'])

        user = session.scalar(stmt)

        poll = Poll(user)
        poll.name = request_body['name']
        poll.description = request_body['description']
        poll.locale = user.locale
        poll.poll_type = PollType.single_vote.name
        poll.number_of_votes = 0
        poll.anonymous = True
        poll.results_visible = False
        poll.set_due_date(parser.parse(request_body['due_date']))
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

        try:
            text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)

            bot = telegram.Bot(token=config['telegram']['api_key'])

            poll_message = bot.send_message(
                text=text,
                chat_id=api_config['seeders_channel_id'],
                reply_markup=keyboard,
                parse_mode='markdown',
                disable_web_page_preview=True,
            )
            poll_message_url = self.create_message_url(poll_message)

            text = f'A discussion thread of the [proposal]({poll_message_url})'
            discussion_message = bot.send_message(
                text=text,
                chat_id=api_config['seeders_channel_id'],
                parse_mode='markdown',
                disable_web_page_preview=True,
            )
            discussion_message_url = self.create_message_url(discussion_message)

            if len(poll.description):
                poll.description += f'\n\nA discussion thread can be find [here]({discussion_message_url})'
            else:
                poll.description = f'A discussion thread can be find [here]({discussion_message_url})'

            text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)
            bot.edit_message_text(
                text=text,
                chat_id=api_config['seeders_channel_id'],
                reply_markup=keyboard,
                parse_mode='markdown',
                disable_web_page_preview=True,
                message_id=poll_message['message_id']
            )

            session.flush()
        except:
            traceback.print_exc()

            session.delete(poll)
            session.commit()

        return 'Ok', 200


    def create_message_url(self, message):
        chat_id = str(message['chat']['id'])
        chat_id = chat_id.removeprefix('-100')

        message_id = message['message_id']
        return f'https://t.me/c/{chat_id}/{message_id}'
