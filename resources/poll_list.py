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
from resources.helpers.option import PollOption

poll_list_model = {
    'id': fields.Integer,
    'chat_id': fields.Integer,
    'poll_message_id': fields.Integer,
    'discussion_message_id': fields.Integer,
}


class PollListApi(Resource):
    @marshal_with(poll_list_model)
    def post(self):
        session = get_session()
        request_body = request.get_json()
        api_config = config['api']

        try:
            stmt = select(User).where(User.username == api_config['admin'])

            user = session.scalar(stmt)
            user.expected_input = None
            user.current_poll = None

            poll = self.create_poll(
                user=user,
                poll_name=request_body['name'],
                poll_description=request_body['description'] if 'description' in request_body else None,
                due_date_string=request_body['due_date'],
                session=session,
            )

            reference = Reference(poll, ReferenceType.api.name, user=user, chat_id=api_config['seeders_chat_id'])
            session.add(reference)
            session.commit()

            poll_message_id, discussion_message_id = self.send_message_to_channel(seeders_chat_id=api_config['seeders_chat_id'], reference=reference, session=session)
        except:
            traceback.print_exc()

            session.delete(poll)
            session.commit()

            abort(404, message='Something went wrong...')

        return {
            'id': poll.id,
            'chat_id': reference.chat_id,
            'poll_message_id': poll_message_id,
            'discussion_message_id': discussion_message_id,
        }, 200

    def create_poll(self, user: User, poll_name: str, poll_description: Optional[str], due_date_string: str, session: Session) -> Poll:
        poll = Poll(user)
        poll.name = poll_name
        poll.description = poll_description
        poll.locale = user.locale
        poll.poll_type = PollType.single_vote.name
        poll.number_of_votes = 0
        poll.anonymous = True
        poll.results_visible = False
        poll.set_due_date(parser.parse(due_date_string))
        poll.allow_new_options = False
        poll.allow_sharing = False
        poll.show_percentage = False
        poll.show_option_votes = True
        poll.european_date_format = user.european_date_format
        poll.permanently_summarized = False
        poll.compact_buttons = False
        poll.summarize = False
        poll.created = True

        session.add(poll)

        for option_to_add in PollOption.ALL_CASES:
            option = add_option(poll, option_to_add, [], False)
            if option is None:
                continue

            session.add(option)

        return poll

    def send_message_to_channel(self, seeders_chat_id: int, reference: Reference, session: Session) -> tuple[int, int]:
        poll = reference.poll
        text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)

        bot = telegram.Bot(token=config['telegram']['api_key'])

        poll_message = bot.send_message(
            text=text,
            chat_id=seeders_chat_id,
            reply_markup=keyboard,
            parse_mode='markdown',
            disable_web_page_preview=True,
            disable_notification=True,
        )
        reference.message_id = poll_message.message_id
        poll_message_url = self.create_message_url(poll_message)

        text = f'Тред с обсуждением этого [предложения]({poll_message_url})'
        discussion_message = bot.send_message(
            text=text,
            chat_id=seeders_chat_id,
            parse_mode='markdown',
            disable_web_page_preview=True,
            disable_notification=True,
            reply_to_message_id=poll_message.message_id,
        )
        discussion_message_url = self.create_message_url(discussion_message)

        description = f'Тред с обсуждением этого [предложения]({discussion_message_url})'
        if poll.description and len(poll.description) > 0:
            poll.description += f'\n\n{description}'
        else:
            poll.description = description

        session.commit()

        text, keyboard = get_poll_text_and_vote_keyboard(session, poll, user=poll.user)
        bot.edit_message_text(
            text=text,
            chat_id=seeders_chat_id,
            message_id=poll_message.message_id,
            reply_markup=keyboard,
            parse_mode='markdown',
            disable_web_page_preview=True,
        )

        return poll_message.message_id, discussion_message.message_id

    def create_message_url(self, message: telegram.Message):
        chat_id = str(message.chat_id)
        chat_id = chat_id.removeprefix('-100')

        message_id = message.message_id
        return f'https://t.me/c/{chat_id}/{message_id}'
