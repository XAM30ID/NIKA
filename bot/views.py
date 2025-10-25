from traceback import format_exc
from asgiref.sync import sync_to_async

from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from telebot.apihelper import ApiTelegramException
from telebot.types import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message, InputMediaPhoto

from bot import bot, logger, UsersStates
from nika.settings import ADMINS
from .handlers.common import format_session_text, format_place_text, replace_message
from .models import GeneralInfo, Session, Place, OptionalInfo

# Получение общей информации
general = GeneralInfo.objects.first()

# Основная клавиатура
first_markup = InlineKeyboardMarkup(row_width=1)
first_markup.add(
    InlineKeyboardButton(text='Смены', callback_data='main.sessions'),
    InlineKeyboardButton(text='Места проведения', callback_data='main.places'),
    InlineKeyboardButton(text='Дополнительная информация', callback_data='main.more_info')
)


def refresh_general():
    '''
        Обновление общей информации
    '''
    global general
    general = GeneralInfo.objects.first()


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    '''
        Установка вебхуков со стороны бота
    '''
    bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}", allowed_updates=['message', 'callback_query'])
    bot.send_message(settings.OWNER_ID, "webhook set")
    return JsonResponse({"message": "OK"}, status=200)


@csrf_exempt
@require_POST
@sync_to_async
def index(request: HttpRequest) -> JsonResponse:
    '''
        Установка вебхуков со стороны сайта
    '''
    if request.META.get("CONTENT_TYPE") != "application/json":
        return JsonResponse({"message": "Bad Request"}, status=403)

    json_string = request.body.decode("utf-8")
    update = Update.de_json(json_string)
    try:
        bot.process_new_updates([update])
    except ApiTelegramException as e:
        logger.error(f"Telegram exception. {e} {format_exc()}")
    except ConnectionError as e:
        logger.error(f"Connection error. {e} {format_exc()}")
    except Exception as e:
        bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)


@bot.message_handler(commands=["start"])
def start_command(message: Message):
    '''
        Команда старт
    '''
    logger.info(f"ОТЛАДКА: Команда /start в чате {message.chat.id} от пользователя {message.from_user.id}")
    bot.send_message(
        chat_id=message.chat.id, 
        text=general.start_text, 
        parse_mode='html', 
        reply_markup=first_markup
        )
    

@bot.message_handler(commands=["help"])
def help_command(message: Message):
    '''
        Команда help
    '''
    bot.send_message(
        chat_id=message.chat.id, 
        text="Отправьте интересующий вопрос или проблему. Этот текст будет перенаправлен для дальнейшей консультации", 
        parse_mode='html', 
        reply_markup=InlineKeyboardMarkup(keyboard=[[InlineKeyboardButton(text='Отмена', callback_data="main.cancel")]])
        )
    bot.set_state(user_id=message.from_user.id, state=UsersStates.help_request, chat_id=message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('main.'))
def main_callbacks(call: CallbackQuery):
    '''
        Обработка нажатий основных Inline-кнопок
    '''
    call_value = call.data.split('.')[-1]
    logger.info(f'ОТЛАДКА: Нажата Inline-кнопка. Значение {call_value}')

    markup = InlineKeyboardMarkup(row_width=1)
    # Возврат в начало
    if call_value == 'cancel':
        replace_message(call, bot, first_markup, general.start_text)
        bot.delete_state(user_id=call.from_user.id, chat_id=call.message.chat.id)

    # Возврат в начало
    if call_value == 'return':
        replace_message(call, bot, first_markup, general.start_text)


    # Отправка списка смен
    if call_value == 'sessions':
        all_sessions = Session.objects.all()
        if len(all_sessions) == 0:
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Смен пока нет)', 
                reply_markup=markup
                )
        
        else:
            for session in all_sessions:
                markup.add(
                    InlineKeyboardButton(text=session.title, callback_data=f's.{session.slug}')
                )
                
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Вот список всех смен:', 
                reply_markup=markup
                )
    
    # Отправка мест проведения
    elif call_value == 'places':
        all_places = Place.objects.all()
        if len(all_places) == 0:
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Мест пока нет)', 
                reply_markup=markup
                )
        
        else:
            for place in all_places:
                markup.add(InlineKeyboardButton(text=place.title, callback_data=f'p.{place.slug}'))
                
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Это места, где обычно проходят смены. О каком месте Вы хотите узнать?', 
                reply_markup=markup
                )   

    # Отправка доп информации 
    elif call_value == 'more_info':
        all_infos = OptionalInfo.objects.all()
        if len(all_infos) == 0:
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Пока что нам нечего Вам рассказать)', 
                reply_markup=markup)
        
        else:
            for info in all_infos:
                markup.add(InlineKeyboardButton(text=info.title, callback_data=f'i.{info.slug}'))
                
            markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Вот статьи, которые помогут Вам ответить на некоторые вопросов:', 
                reply_markup=markup
                )
            

@bot.callback_query_handler(func=lambda call: call.data.startswith('s.'))
def session_callback(call: CallbackQuery):
    '''
        Подробнее о смене
    '''
    markup = InlineKeyboardMarkup(row_width=1)

    session_slug = call.data.split('.')[-1]

    if session_slug == 'return':
        all_sessions = Session.objects.all()

        for session in all_sessions:
            markup.add(
                InlineKeyboardButton(text=session.title, callback_data=f's.{session.slug}')
            )
            
        markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))

        replace_message(call, bot, markup, 'Вот список смен')
    else:
        session = Session.objects.get(slug=session_slug)

        if not session.form_url is None:
            if session.form_url.strip() != '' and not session.form_url is None:
                markup.add(InlineKeyboardButton(text='Записаться!', url=session.form_url))

        markup.add(InlineKeyboardButton(text='К списку смен 📃', callback_data='s.return'))
        markup.add(InlineKeyboardButton(text='В начало ↩️', callback_data='main.return'))

        if session.pk:
            if not session.image is None and not session.image == '':
                with open(f'{settings.BASE_DIR}//{session.image.url}', 'rb') as file:
                    try:
                        bot.delete_message(
                            chat_id=call.message.chat.id, 
                            message_id=call.message.id
                        )
                    except Exception as e:
                        logger.error(f'При удалении сообщения возникла ошибка: {e}')
                    bot.send_photo(
                        chat_id=call.message.chat.id, 
                        photo=file,
                        caption=format_session_text(session=session),
                        reply_markup=markup,
                        parse_mode='html'
                        )
            else:
                return bot.edit_message_text(
                    chat_id=call.message.chat.id, 
                    message_id=call.message.message_id, 
                    text=format_session_text(session=session),
                    reply_markup=markup,
                    parse_mode='html'
                    )

        else:
            return bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text='Приносим извинения, смена не найдена(', 
                reply_markup=markup
                )
        

@bot.callback_query_handler(func=lambda call: call.data.startswith('p.'))
def place_callback(call: CallbackQuery):
    '''
        Подробнее о месте проведения
    '''
    markup = InlineKeyboardMarkup(row_width=1)

    place_slug = call.data.split('.')[-1]

    if place_slug == 'return':
        all_places = Place.objects.all()

        for place in all_places:
            markup.add(
                InlineKeyboardButton(text=place.title, callback_data=f'p.{place.slug}')
            )
            
        markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))
        if call.message.content_type == 'location':
            replace_message(call, bot, markup, 'Это места, где обычно проходят смены. О каком месте Вы хотите узнать?', 2)
        else:
            replace_message(call, bot, markup, 'Это места, где обычно проходят смены. О каком месте Вы хотите узнать?', 1)
    else:
        markup.add(InlineKeyboardButton(text='К списку мест 📃', callback_data='p.return'))
        markup.add(InlineKeyboardButton(text='В начало ↩️', callback_data='main.return'))

        place = Place.objects.get(slug=place_slug)
        
        if place.pk:

            if not place.latitude is None and not place.longitude is None:
                replace_message(call, bot, None, format_place_text(place=place))
                return bot.send_location(
                    chat_id=call.message.chat.id,
                    latitude=place.latitude,
                    longitude=place.longitude,
                    reply_markup=markup
                )
            else:
                return replace_message(call, bot, markup, format_place_text(place=place))

        else:
            return replace_message(call, bot, markup, 'Приносим извинения, данное место не найдено')


@bot.callback_query_handler(func=lambda call: call.data.startswith('i.'))
def optional_info_callback(call: CallbackQuery):
    '''
        Дополнительная информация
    '''
    markup = InlineKeyboardMarkup(row_width=1)

    info_slug = call.data.split('.')[-1]
    print(info_slug)
    if info_slug == 'return':
        all_infos = OptionalInfo.objects.all()

        for info in all_infos:
            markup.add(
                InlineKeyboardButton(text=info.title, callback_data=f'i.{info.slug}')
            )
            
        markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='main.return'))
        replace_message(call, bot, markup, 'Вот статьи, которые помогут Вам ответить на некоторые вопросов:')
    
    else:
        markup.add(InlineKeyboardButton(text='Вернуться ↩️', callback_data='i.return'))
        info = OptionalInfo.objects.get(slug=info_slug)
        print(info.is_photo, info.file)
        if info.is_photo and not info.file is None and not info.file == '':
            with open(f'{settings.BASE_DIR}//{info.file.url}', 'rb') as file:
                    try:
                        bot.delete_message(
                            chat_id=call.message.chat.id, 
                            message_id=call.message.id
                        )
                    except Exception as e:
                        logger.error(f'При удалении сообщения возникла ошибка: {e}')
                    bot.send_photo(
                        chat_id=call.message.chat.id, 
                        photo=file,
                        caption=info.text,
                        reply_markup=markup,
                        parse_mode='html'
                        )
        
        else:
            if not info.file is None and not info.file == '':
                print(info.is_photo, info.file)
                # replace_message(call, bot, None, info.text)
                try:
                    bot.delete_message(
                        chat_id=call.message.chat.id, 
                        message_id=call.message.message_id
                        )
                        
                except Exception as e:
                    print(e)
                
                with open(f'{settings.BASE_DIR}//{info.file.url}', 'rb') as file:
                    print(file)
                    bot.send_document(
                        chat_id=call.message.chat.id,
                        document=file,
                        caption=info.text,
                        reply_markup=markup,
                        parse_mode='html'
                    )
            else:
                replace_message(call, bot, markup, info.text)

        
        
@bot.message_handler()
def messages_handler(message: Message):
    state = bot.get_state(user_id=message.from_user.id, chat_id=message.chat.id)
    if state == UsersStates.help_request.name:
        text = f'<strong>Пользователь @{message.from_user.username}</strong> попросил о помощи:\n\n' \
                f'"{message.text}"'
        for admin in ADMINS:
            try:
                bot.send_message(chat_id=admin, text=text, parse_mode='html')
            except Exception as e:
                print(e)
        bot.send_message(
            chat_id=message.chat.id, 
            text='Ваше сообщение доставлено в службу поддержки. Вы так же можете написать лично:\n\n' \
            '<a href="t.me/oksanozka1207">Оксана Николаевна</a>\n' \
            '<a href="t.me/zilfia17">Зульфия Ахнафовна</a>',
            parse_mode='html',
            disable_web_page_preview=True
            )