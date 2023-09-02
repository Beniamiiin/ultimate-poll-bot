import traceback
from typing import Optional

import telegram
from dateutil import parser
from flask import request
from flask_restful import Resource, marshal_with, fields, abort
from sqlalchemy import select
from sqlalchemy.orm import Session

from pollbot.config import config
from pollbot.db import get_session
from pollbot.display.poll.compilation import get_poll_text_and_vote_keyboard
from pollbot.enums import ReferenceType, PollType
from pollbot.models import Poll, User, Reference
from pollbot.poll.option import add_option

poll_model = {
    'id': fields.Integer,
}


class PollApi(Resource):
    @marshal_with(poll_model)
    def post(self):
        session = get_session()
        request_body = request.get_json()
        api_config = config['api']

        try:
            poll = self.create_poll(
                admin_username=api_config['admin'],
                poll_name=request_body['name'],
                poll_description=request_body['description'] if 'description' in request_body else None,
                due_date_string=request_body['due_date'],
                session=session,
            )

            self.send_message_to_channel(seeders_channel_id=api_config['seeders_channel_id'], poll=poll, session=session)
        except:
            traceback.print_exc()

            session.delete(poll)
            session.commit()

            abort(404, message='Something went wrong...')

        return poll, 200

    def create_poll(self, admin_username: str, poll_name: str, poll_description: Optional[str], due_date_string: str,
                    session: Session) -> Poll:
        stmt = select(User).where(User.username == admin_username)

        user = session.scalar(stmt)

        poll = Poll(user)
        poll.name = poll_name
        poll.description = poll_description
        poll.locale = user.locale
        poll.poll_type = PollType.single_vote.name
        poll.number_of_votes = 0
        poll.anonymous = True
        poll.results_visible = True
        poll.set_due_date(parser.parse(due_date_string))
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

        reference = Reference(poll, ReferenceType.admin.name, user=user, message_id=1)
        session.add(reference)
        session.commit()

        return poll

    def send_message_to_channel(self, seeders_channel_id: int, poll: Poll, session: Session):
        text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)

        bot = telegram.Bot(token=config['telegram']['api_key'])

        poll_message = bot.send_message(
            text=text,
            chat_id=seeders_channel_id,
            reply_markup=keyboard,
            parse_mode='markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
        poll_message_url = self.create_message_url(poll_message)

        text = f'A discussion thread of the [proposal]({poll_message_url})'
        discussion_message = bot.send_message(
            text=text,
            chat_id=seeders_channel_id,
            parse_mode='markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
        discussion_message_url = self.create_message_url(discussion_message)

        if poll.description and len(poll.description) > 0:
            poll.description += f'\n\nA discussion thread can be find [here]({discussion_message_url})'
        else:
            poll.description = f'A discussion thread can be find [here]({discussion_message_url})'

        session.commit()
        
        text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)
        bot.edit_message_text(
            text=text,
            chat_id=seeders_channel_id,
            message_id=poll_message['message_id'],
            reply_markup=keyboard,
            parse_mode='markdown',
            disable_web_page_preview=True,
        )

    def create_message_url(self, message):
        chat_id = str(message['chat']['id'])
        chat_id = chat_id.removeprefix('-100')

        message_id = message['message_id']
        return f'https://t.me/c/{chat_id}/{message_id}'
