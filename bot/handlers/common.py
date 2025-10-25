from ..models import Session, Place


def replace_message(call, bot, markup, text, messages_count=1):
    try:
        return bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id, 
            text=text, 
            reply_markup=markup,
            parse_mode='html'
            )
            
    except Exception as e:
        ids = [i for i in range(call.message.message_id, call.message.message_id - messages_count, -1)] 
        print(ids)
        bot.delete_messages(
            chat_id=call.message.chat.id, 
            message_ids=ids[::-1],
        )
        return bot.send_message(
                chat_id=call.message.chat.id, 
                text=text, 
                reply_markup=markup,
                parse_mode='html'
                )


def format_session_text(session: Session):
    text = f'🏕️ Смена <strong>«{session.title}»</strong>'
    if not session.place is None:
        text += f'\n\n🗺️ Место проведения: <strong>{session.place.title}</strong>'
    
    if not (session.start_date is None or session.end_date is None):
        text += f"\n📆 Даты: <strong>{str(session.start_date).replace('-', '.')}–{str(session.end_date).replace('-', '.')}</strong>"
    
    if not session.description is None:
        text += f'\n\n{session.description}'
        
    return text


def format_place_text(place: Place):
    text = f'<strong>«{place.title}»</strong>'

    if not place.description is None:
        text += f'\n\n{place.description}'
    
    return text